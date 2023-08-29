import subprocess
import json
import re
import os


def search_pr(search, gh_cmd_start, limit=20):
  """ Search for pr using gh utility """
  cmd = gh_cmd_start + ['pr',
      'list',
      '--search', search,
      '--limit', str(limit),
      '--json', 'number,autoMergeRequest,mergeStateStatus,reviews,reviewDecision,url'
  ]
  data = json.loads(subprocess.check_output(cmd, text=True))
  return data

def pick_needle(incomming, min_reviews=1):
  """
  Returns (first possible)
  - oldest PR with at least min_reviews in CLEAN state (=can be merged)
  - oldest PR with at least min_reviews in BEHIND state (= needs rebase)
  - None 

  Prints info about skipped PR (not enough reviews or different state)
  """
  oldest_behind = None
  for candidate in incomming:
    if len(candidate['reviews']) < min_reviews:
      print(f'SKIP: {candidate["url"]} with only {len(candidate["reviews"])} reviews')
      continue
    if candidate['mergeStateStatus'] == 'CLEAN':
      return candidate
    if candidate['mergeStateStatus'] == 'BEHIND':
      if oldest_behind is None:
        oldest_behind = candidate
    print(f'{candidate["mergeStateStatus"]} mergeStateStatus - PR#{candidate["number"]}')
  return oldest_behind

def update_pr(pr,gh_cmd_start):
  """ Merge (using automerge) or rebase the PR """

  if pr['mergeStateStatus'] == 'CLEAN':
    # Do not set automerge if it is already set
    # GH should merge it faster than this script but better be safe
    if not pr['autoMergeRequest']:
      subprocess.check_call(
        gh_cmd_start + ['pr',
          "merge",
          f"{pr['number']}",
         "--rebase", "--auto"
        ])
  elif pr['mergeStateStatus'] == 'BEHIND':
    match = re.search(r'github\.com/([^/]+/[^/]+)/', pr['url'])
    if match:
      repo = match.group(1)
      subprocess.check_call([
        "gh",
        "api",
        "--method", "PUT",
        "-H", "Accept: application/vnd.github+json",
        "-H", "X-GitHub-Api-Version: 2022-11-28",
        "-f", "update_method=rebase",
        f"/repos/{repo}/pulls/{pr['number']}/update-branch"
      ])
  else:
    raise RuntimeError(f"How could we get here? {pr}")

def main(dry,min_reviews, repo, label):
  search_query = f'is:open review:approved label:"{label}" sort:created-asc'
  gh_with_repo = [ 'gh'] + (['-R', repo] if repo else [])

  candidate_pull_requests = search_pr(search=search_query, gh_cmd_start=gh_with_repo)
  if not candidate_pull_requests:
    print(f"No PR found for '{search_query}'")
    return 

  picked_pr = pick_needle(candidate_pull_requests, min_reviews=min_reviews)
  if picked_pr is None:
    print('No PR can be rebased or merged')
    return
  print(f'Update PR#{picked_pr["number"]}')
  if dry:
    return
  update_pr(picked_pr, gh_cmd_start=gh_with_repo)
 

if __name__ == "__main__":
  # Options from the environment
  dry = os.environ.get('DRY', '0') != '0'
  min_reviews = int(os.environ.get('MIN_REVIEWS', '1'))
  repo = os.environ.get('REPO', None)
  label = os.environ.get('LABEL', 'ready for merge')

  main(dry=dry, min_reviews=min_reviews, repo=repo, label=label)

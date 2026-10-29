import json
import urllib.error
import urllib.parse
import urllib.request


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    API = "https://api.github.com"

    def __init__(self, token: str):
        self.token = token.strip()

    def request(self, method, path, payload=None, params=None):
        if params:
            path += ("&" if "?" in path else "?") + urllib.parse.urlencode(params)
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.API + path,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "GitHub-Command-Center-Python",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read()
                return None if not raw else json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                body = json.loads(exc.read().decode("utf-8"))
                message = body.get("message", str(exc))
            except Exception:
                message = str(exc)
            raise GitHubError(f"GitHub API {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"Network error: {exc.reason}") from exc

    def get_user(self):
        return self.request("GET", "/user")

    def get_repositories(self):
        all_repos = []
        page = 1
        while True:
            batch = self.request("GET", "/user/repos", params={
                "per_page": 100, "page": page, "sort": "updated",
                "affiliation": "owner,collaborator,organization_member"
            })
            all_repos.extend(batch)
            if len(batch) < 100:
                return all_repos
            page += 1

    def get_events(self, login):
        return self.request("GET", f"/users/{urllib.parse.quote(login)}/events", params={"per_page": 30})

    def get_rate_limit(self):
        return self.request("GET", "/rate_limit")["rate"]

    def create_repository(self, name, description="", private=True, auto_init=True):
        return self.request("POST", "/user/repos", {
            "name": name, "description": description,
            "private": private, "auto_init": auto_init,
        })

    def create_issue(self, full_name, title, body=""):
        owner, repo = full_name.split("/", 1)
        return self.request("POST", f"/repos/{owner}/{repo}/issues", {"title": title, "body": body})

    def get_releases(self, full_name):
        return self.request("GET", f"/repos/{full_name}/releases", params={"per_page": 20})

# Sorting Explained

## `/live/top` Endpoint

- **Sort by Viewers (default):**

  ```bash
  curl "http://localhost:8000/live/top?sort_by=viewers&limit=10"
  ```

  Returns streamers sorted by current viewer count.

- **Sort by Followers:**
  ```bash
  curl "http://localhost:8000/live/top?sort_by=followers&limit=10"
  ```
  Returns streamers sorted by total follower count.

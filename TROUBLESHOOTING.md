# Troubleshooting

## Common Issues

### Twitch API Authentication

- **Check credentials:**
  ```bash
  cat .env | grep TWITCH
  ```
- **Restart collector:**
  ```bash
  docker-compose restart collector
  ```

### Database Connection Errors

- Ensure database service is running.

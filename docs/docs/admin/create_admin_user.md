# Creating an admin user

**Note:** Only someone with access to the server (SSH or Portainer console) can do this.
Admin accounts are intentional not self-serve.

## Steps

1. Ensure all containers are running:

   ```bash
   docker compose ps
   ```

2. Open a shell inside the API container:

   ```bash
   docker exec -it papadam-api bash
   ```

3. Create the superuser:

   ```bash
   python manage.py createsuperuser
   ```

   Follow the prompts. Use a real email — it is displayed to users as a support contact.

4. Exit the container:

   ```bash
   exit
   ```

5. Open the admin site at `https://your-domain/nimda/`

## What admins can do

- Create and manage groups
- Manage users and group membership
- Withhold or restore content at the instance level
- Trigger exports and view import/export history
- Inspect annotation and media records

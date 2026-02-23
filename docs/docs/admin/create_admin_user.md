## Creating Admin user

**Known Limit** : Only instance admin with access to the server can do the following actions. It is intended that way and will not change.

### Steps to create a super user

1. cd to your papad-docker repository
2. ```docker-compose ps``` to ensure all your containers are running
3. ``` docker exec -it papad-docker_papad_api_1  bash ``` this command will take you inside the api container
4. ``` pip install -r requirements-dev.txt ``` This will install all required developer based python dependencies. We are working on overcoming this step but is currently not ready
5. ``` python manage-prod.py createsuperuser ``` Follow the on-screen instructions and please ensure to give an accurate email and name. We display this email and name to all users to ensure they know who to contact for support.
6. ``` exit ```

Now open <your-instanace-url>/nimda/ for the admin site to load

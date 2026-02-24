# Authentication

papadam uses username and password authentication.

## Signing up

Click **Login** in the navigation bar, then **Create new account**. You will need:

- Username
- Password
- Email
- First name
- Last name

![Sign up form](/static/authentication/user_register.png)

**Note:** There is no email verification. papadam is often deployed on local networks
where users may not have email access. Authentication is a system of trust,
not identity verification.

## Logging in

Enter your username and password on the login page.

![Login form](/static/authentication/user_login.png)

After logging in you are taken to the main page showing your groups.

![Dashboard after login](/static/authentication/user_dashboard.png)

## Logging out

Click **Logout** in the navigation bar. Your session tokens are cleared immediately.

## Forgotten password

Contact your instance admin. Self-service password reset is not yet available.

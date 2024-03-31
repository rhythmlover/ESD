# Club Ticketing
The business scenario covers a ticketing service for clubs aimed at streamlining the event processes and improving customer experience from the purchase of tickets to post-event feedback and reviews. Through the use of a ticketing service, we will be able to provide customers with an easy and effortless way to gain entry into the club by incorporating Singpass. Similarly, clubs will benefit from the ticketing service by having a digitalised solution for their everyday operations and data analysis for future development.

## Used Technology
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![RabbitMQ](https://img.shields.io/badge/Rabbitmq-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-e37b3b.svg?style=for-the-badge&logo=firebase&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Kong](https://img.shields.io/badge/kong-0a473a.svg?style=for-the-badge&logo=kong&logoColor=white)

## Notes
- All data is being stored in firebase, no SQL files are required to run.
- For the email service, we have implemented it such that the confirmation emails are only sent to our team's test emails. If you wish to test our email service, please contact any of our team members and we will add you accordingly to our internal database.

## Microservices setup
```
cd svcs
docker-compose build
docker-compose up
```

## Additional setup
```
cd svcs
```
- In compose.yaml, head to Email Microservice section and fill in an SendGrid API key
- An API key can be generated at https://sendgrid.com/en-us

## Testing
```
cd tests
```
- Drag the respective JSON files into Postman

## Front End
```
cd FrontEnd
```
- login.html is the root page

## Credits

G8T8 - Nigel, Ethan, Dominic, Eugene, Xinyong, Abhay
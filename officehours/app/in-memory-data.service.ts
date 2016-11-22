import { InMemoryDbService } from 'angular-in-memory-web-api';

export class InMemoryDataService implements InMemoryDbService {
  createDb() {
    let contacts = [
        {id: 10, name: 'Dr. Strange', email: 'drstrange@x.edu', phone: '123-456-7890'},
        {id: 11, name: 'Prof. Xavier', email: 'profx@x.edu', phone: '123-456-7890'},
    ]

    let officehours = [
        {id: 10, fromTime: '8:00am', toTime: '9:00am', days: ['Monday', 'Wednesday']},
        {id: 11, fromTime: '11:00am', toTime: '12:00pm', days: ['Tuesday', 'Thursday']},
    ]
    return {contacts: contacts, officehours: officehours};
  }
}

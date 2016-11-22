import { Injectable } from '@angular/core';
import { Headers, Http } from '@angular/http';

import 'rxjs/add/operator/toPromise';

import { Contact, OfficeHours } from './models';


@Injectable()
export class ContactService {

    private headers = new Headers({'Content-Type': 'application/json'});
    private contactsUrl = 'app/contacts';  // URL to web api

    constructor(private http: Http) {}

    getContacts(): Promise<Contact[]> {
        return this.http.get(this.contactsUrl)
                   .toPromise()
                   .then(response => response.json().data as Contact[])
                   .catch(this.handleError);
    }

    private handleError(error: any): Promise<any> {
        console.error("An error occurred", error); // for demo purposes
        return Promise.reject(error.message || error);
    }

    getContact(id: number): Promise<Contact> {
        return this.getContacts()
                   .then(contacts => contacts.find(contact => contact.id === id));
    }

    update(contact: Contact): Promise<Contact> {
        const url = `${this.contactsUrl}/${contact.id}`;
        return this.http
                   .put(url, JSON.stringify(contact), {headers: this.headers})
                   .toPromise()
                   .then(() => contact)
                   .catch(this.handleError);
    }

    create(name: string, email: string, phone: string): Promise<Contact> {
        return this.http
            .post(
                this.contactsUrl,
                JSON.stringify({name: name, email: email, phone: phone}),
                {headers: this.headers})
            .toPromise()
            .then(res => res.json().data)
            .catch(this.handleError);
    }

    /*
    delete(id: number): Promise<void> {
        const url = `${this.contactsUrl}/${id}`;
        return this.http.delete(url, {headers: this.headers})
            .toPromise()
            .then(() => null)
            .catch(this.handleError);
    }
    */
}

@Injectable()
export class OfficeHoursService {

    private headers = new Headers({'Content-Type': 'application/json'});
    private officeHoursUrl = 'app/officehours';  // URL to web api

    constructor(private http: Http) {}

    getOfficeHours(): Promise<OfficeHours[]> {
        return this.http.get(this.officeHoursUrl)
                   .toPromise()
                   .then(response => response.json().data as OfficeHours[])
                   .catch(this.handleError);
    }

    private handleError(error: any): Promise<any> {
        console.error("An error occurred", error); // for demo purposes
        return Promise.reject(error.message || error);
    }

    update(hours: OfficeHours): Promise<OfficeHours> {
        const url = `${this.officeHoursUrl}/${hours.id}`;
        return this.http
                   .put(url, JSON.stringify(hours), {headers: this.headers})
                   .toPromise()
                   .then(() => hours)
                   .catch(this.handleError);
    }

    /*
    create(name: string, email: string, phone: string): Promise<OfficeHours> {
        return this.http
            .post(
                this.officeHours,
                JSON.stringify({ TODO }),
                {headers: this.headers})
            .toPromise()
            .then(res => res.json().data)
            .catch(this.handleError);
    }

    delete(id: number): Promise<void> {
        const url = `${this.hours}/${id}`;
        return this.http.delete(url, {headers: this.headers})
            .toPromise()
            .then(() => null)
            .catch(this.handleError);
    }
    */
}

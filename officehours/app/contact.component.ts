import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';

import { Contact } from './models';
import { ContactService } from './models.service';

import 'rxjs/add/operator/switchMap';


@Component({
	moduleId: module.id,
    selector: 'contact-info',
    templateUrl: 'contact.component.html',
    //styleUrls: [ 'contact.component.css' ]
})

export class ContactComponent implements OnInit {
    contact: Contact
    contacts: Contact[]

    constructor(
        private contactService: ContactService,
        private router: Router,
        private route: ActivatedRoute) {}


    ngOnInit(): void {
        // TODO: How to get the *current* contact's info rather than all?
        this.contactService.getContacts()
            .then(contacts => {
                this.contacts = contacts;
                console.log("GOT: ", contacts);
            });
    }

    gotoNext() {
        this.router.navigate(['officehours']);
    }

    save(): void {
        this.contactService.update(this.contact)
            .then(() => this.gotoNext());
    }

    add(name: string, email: string, phone: string): void {
        name = name.trim()
        email = email.trim()
        phone = phone.trim()
        if (!name || !email || !phone) { return; }

        this.contactService.create(name, email, phone)
            .then(contact => {
                this.contact = contact;
                this.gotoNext();
            });
    }
}

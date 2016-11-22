import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { OfficeHours } from './models';
import { OfficeHoursService } from './models.service';

import 'rxjs/add/operator/switchMap';


@Component({
	moduleId: module.id,
    selector: 'officehours',
    templateUrl: 'officehours.component.html',
    //styleUrls: [ 'officehours.component.css' ]
})

export class OfficeHoursComponent implements OnInit {
    hours: OfficeHours
    ohCollection: OfficeHours[]

    constructor(
        private officeHoursService: OfficeHoursService,
        private route: ActivatedRoute) {}


    ngOnInit(): void {
        // TODO: get the current officehours?
        this.officeHoursService.getOfficeHours()
            .then(officehours => this.ohCollection = officehours);
    }

    gotoNext() {
        console.log("TODO: go to the next thing")
    }

    /*
    save(): void {
        this.officehoursService.update(this.officehours)
            .then(() => this.gotoNext());
    }

    add(name: string, email: string, phone: string): void {
        name = name.trim()
        email = email.trim()
        phone = phone.trim()
        console.log("ADDING: ", name, email, phone);
        if (!name || !email || !phone) { return; }

        this.officehoursService.create(name, email, phone)
            .then(officehours => {this.officehours = officehours; this.gotoNext();});
    }
    */
}

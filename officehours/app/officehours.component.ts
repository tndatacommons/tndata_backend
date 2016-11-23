import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';

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
    checkboxes = [
        {label: 'Sunday'},
        {label: 'Monday'},
        {label: 'Tuesday'},
        {label: 'Wednesday'},
        {label: 'Thursday'},
        {label: 'Friday'},
        {label: 'Saturday'}
    ]

    constructor(
        private officeHoursService: OfficeHoursService,
        private router: Router,
        private route: ActivatedRoute) {}

    ngOnInit(): void {
        // TODO: get the current officehours?
        this.officeHoursService.getOfficeHours()
            .then(officehours => this.ohCollection = officehours);
    }

    addAnother() {
        this.hours = null;
        this.router.navigate(['officehours']);
    }

    gotoNext() {
        console.log("hours: ", this.hours);
        console.log("TODO: go to the next thing");
        //this.router.navigate(['TODO']);
    }

    save(): void {
        this.officeHoursService.update(this.hours)
            .then(() => {
                //this.gotoNext()
                console.log("Saved: ", this.hours);
             });
    }

    //add(fromTime: string, toTime: string, days: string[]): void {
    add(fromTime: string, toTime: string): void {
        console.log("CLICKED ADD");
        console.log("fromTime: ", fromTime);
        console.log("toTime: ", toTime);

        fromTime = fromTime.trim()
        toTime = toTime.trim()
        let days = [];

        //this.checkboxes.some(cb => {
            //if(cb.state) {
                //days.push(cb.label);
            //}
        //})

        console.log("ADDING: ", fromTime, toTime);
        console.log("Selected Days: ", days);

        //if (!name || !email || !phone) { return; }
        //this.officeHoursService.create(fromTime, toTime, days)
            //.then(officehours => {this.hours = officehours; this.gotoNext();});
    }
}

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
    //hours: OfficeHours
    fromTimeText = ""
    toTimeText = ""

    ohCollection: OfficeHours[]
    checkboxes = [
        {label: 'Sunday', state: false},
        {label: 'Monday', state: false},
        {label: 'Tuesday', state: false},
        {label: 'Wednesday', state: false},
        {label: 'Thursday', state: false},
        {label: 'Friday', state: false},
        {label: 'Saturday', state: false}
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
        //this.hours = null;
        this.router.navigate(['officehours']);
    }

    gotoNext() {
        console.log("TODO: go to the next thing");
        //this.router.navigate(['TODO']);
    }

    save(): void {
        console.log("Clicked save() ");
        //this.officeHoursService.update(this.hours)
            //.then(() => {
                //console.log("Saved: ", this.hours);
             //});
    }

    add(): void {
        // XXX: Why can I do `fromTime.value` here, and not in
        // XXX: the template like in previous examples?
        console.log("CLICKED ADD: ", this.fromTimeText, this.toTimeText);

        //let hours = new OfficeHours();

        /*
        // XXX: THIS always causes errors when I stop/restart `npm start`
        let days = [];
        this.checkboxes.some(cb => {
            console.log(cb);
            if(cb.state) {
                //hours.addDay(cb.label);
                console.log({label: cb.label, state: cb.state});
                days.push(cb.label);
            }
        });
        console.log("Days: ", days);
        */

        //console.log("hours: ", hours);
        //let hours = new OfficeHours(this.fromTimeText, this.toTimeText);


        //this.officeHoursService.create(ft, tt, days)
            //.then(officehours => {
                //this.hours = officehours;
            //});
    }
}

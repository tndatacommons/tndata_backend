"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var core_1 = require('@angular/core');
var router_1 = require('@angular/router');
var models_service_1 = require('./models.service');
require('rxjs/add/operator/switchMap');
var OfficeHoursComponent = (function () {
    function OfficeHoursComponent(officeHoursService, router, route) {
        this.officeHoursService = officeHoursService;
        this.router = router;
        this.route = route;
        //hours: OfficeHours
        this.fromTimeText = "";
        this.toTimeText = "";
        this.checkboxes = [
            { label: 'Sunday', state: false },
            { label: 'Monday', state: false },
            { label: 'Tuesday', state: false },
            { label: 'Wednesday', state: false },
            { label: 'Thursday', state: false },
            { label: 'Friday', state: false },
            { label: 'Saturday', state: false }
        ];
    }
    OfficeHoursComponent.prototype.ngOnInit = function () {
        var _this = this;
        // TODO: get the current officehours?
        this.officeHoursService.getOfficeHours()
            .then(function (officehours) { return _this.ohCollection = officehours; });
    };
    OfficeHoursComponent.prototype.addAnother = function () {
        //this.hours = null;
        this.router.navigate(['officehours']);
    };
    OfficeHoursComponent.prototype.gotoNext = function () {
        console.log("TODO: go to the next thing");
        //this.router.navigate(['TODO']);
    };
    OfficeHoursComponent.prototype.save = function () {
        console.log("Clicked save() ");
        //this.officeHoursService.update(this.hours)
        //.then(() => {
        //console.log("Saved: ", this.hours);
        //});
    };
    OfficeHoursComponent.prototype.add = function () {
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
    };
    OfficeHoursComponent = __decorate([
        core_1.Component({
            moduleId: module.id,
            selector: 'officehours',
            templateUrl: 'officehours.component.html',
        }), 
        __metadata('design:paramtypes', [models_service_1.OfficeHoursService, router_1.Router, router_1.ActivatedRoute])
    ], OfficeHoursComponent);
    return OfficeHoursComponent;
}());
exports.OfficeHoursComponent = OfficeHoursComponent;
//# sourceMappingURL=officehours.component.js.map
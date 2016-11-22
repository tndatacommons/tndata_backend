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
    function OfficeHoursComponent(officeHoursService, route) {
        this.officeHoursService = officeHoursService;
        this.route = route;
    }
    OfficeHoursComponent.prototype.ngOnInit = function () {
        var _this = this;
        // TODO: get the current officehours?
        this.officeHoursService.getOfficeHours()
            .then(function (officehours) { return _this.ohCollection = officehours; });
    };
    OfficeHoursComponent.prototype.gotoNext = function () {
        console.log("TODO: go to the next thing");
    };
    OfficeHoursComponent = __decorate([
        core_1.Component({
            moduleId: module.id,
            selector: 'officehours',
            templateUrl: 'officehours.component.html',
        }), 
        __metadata('design:paramtypes', [models_service_1.OfficeHoursService, router_1.ActivatedRoute])
    ], OfficeHoursComponent);
    return OfficeHoursComponent;
}());
exports.OfficeHoursComponent = OfficeHoursComponent;
//# sourceMappingURL=officehours.component.js.map
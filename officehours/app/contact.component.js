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
var ContactComponent = (function () {
    function ContactComponent(contactService, router, route) {
        this.contactService = contactService;
        this.router = router;
        this.route = route;
    }
    ContactComponent.prototype.ngOnInit = function () {
        var _this = this;
        // TODO: How to get the *current* contact's info rather than all?
        this.contactService.getContacts()
            .then(function (contacts) {
            _this.contacts = contacts;
            console.log("GOT: ", contacts);
        });
    };
    ContactComponent.prototype.gotoNext = function () {
        this.router.navigate(['officehours']);
    };
    ContactComponent.prototype.save = function () {
        var _this = this;
        this.contactService.update(this.contact)
            .then(function () { return _this.gotoNext(); });
    };
    ContactComponent.prototype.add = function (name, email, phone) {
        var _this = this;
        name = name.trim();
        email = email.trim();
        phone = phone.trim();
        if (!name || !email || !phone) {
            return;
        }
        this.contactService.create(name, email, phone)
            .then(function (contact) {
            _this.contact = contact;
            _this.gotoNext();
        });
    };
    ContactComponent = __decorate([
        core_1.Component({
            moduleId: module.id,
            selector: 'contact-info',
            templateUrl: 'contact.component.html',
        }), 
        __metadata('design:paramtypes', [models_service_1.ContactService, router_1.Router, router_1.ActivatedRoute])
    ], ContactComponent);
    return ContactComponent;
}());
exports.ContactComponent = ContactComponent;
//# sourceMappingURL=contact.component.js.map
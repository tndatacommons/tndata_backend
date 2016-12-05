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
var http_1 = require('@angular/http');
require('rxjs/add/operator/toPromise');
var ContactService = (function () {
    function ContactService(http) {
        this.http = http;
        this.headers = new http_1.Headers({ 'Content-Type': 'application/json' });
        this.contactsUrl = 'app/contacts'; // URL to web api
    }
    ContactService.prototype.getContacts = function () {
        return this.http.get(this.contactsUrl)
            .toPromise()
            .then(function (response) { return response.json().data; })
            .catch(this.handleError);
    };
    ContactService.prototype.handleError = function (error) {
        console.error("An error occurred", error); // for demo purposes
        return Promise.reject(error.message || error);
    };
    ContactService.prototype.getContact = function (id) {
        return this.getContacts()
            .then(function (contacts) { return contacts.find(function (contact) { return contact.id === id; }); });
    };
    ContactService.prototype.update = function (contact) {
        var url = this.contactsUrl + "/" + contact.id;
        return this.http
            .put(url, JSON.stringify(contact), { headers: this.headers })
            .toPromise()
            .then(function () { return contact; })
            .catch(this.handleError);
    };
    ContactService.prototype.create = function (name, email, phone) {
        return this.http
            .post(this.contactsUrl, JSON.stringify({ name: name, email: email, phone: phone }), { headers: this.headers })
            .toPromise()
            .then(function (res) { return res.json().data; })
            .catch(this.handleError);
    };
    ContactService = __decorate([
        core_1.Injectable(), 
        __metadata('design:paramtypes', [http_1.Http])
    ], ContactService);
    return ContactService;
}());
exports.ContactService = ContactService;
var OfficeHoursService = (function () {
    function OfficeHoursService(http) {
        this.http = http;
        this.headers = new http_1.Headers({ 'Content-Type': 'application/json' });
        this.officeHoursUrl = 'app/officehours'; // URL to web api
    }
    OfficeHoursService.prototype.getOfficeHours = function () {
        return this.http.get(this.officeHoursUrl)
            .toPromise()
            .then(function (response) { return response.json().data; })
            .catch(this.handleError);
    };
    OfficeHoursService.prototype.handleError = function (error) {
        console.error("An error occurred", error); // for demo purposes
        return Promise.reject(error.message || error);
    };
    OfficeHoursService.prototype.update = function (hours) {
        var url = this.officeHoursUrl + "/" + hours.id;
        return this.http
            .put(url, JSON.stringify(hours), { headers: this.headers })
            .toPromise()
            .then(function () { return hours; })
            .catch(this.handleError);
    };
    OfficeHoursService.prototype.create = function (fromTime, toTime, days) {
        return this.http
            .post(this.officeHoursUrl, JSON.stringify({ fromTime: fromTime, toTime: toTime, days: days }), { headers: this.headers })
            .toPromise()
            .then(function (res) { return res.json().data; })
            .catch(this.handleError);
    };
    OfficeHoursService = __decorate([
        core_1.Injectable(), 
        __metadata('design:paramtypes', [http_1.Http])
    ], OfficeHoursService);
    return OfficeHoursService;
}());
exports.OfficeHoursService = OfficeHoursService;
//# sourceMappingURL=models.service.js.map
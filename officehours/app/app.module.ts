import { NgModule }      from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';

import { AppRoutingModule } from './app-routing.module';

// Imports for loading & configuring the in-memory web api
import { InMemoryWebApiModule } from 'angular-in-memory-web-api';
import { InMemoryDataService }  from './in-memory-data.service';

import { AppComponent } from './app.component';
import { WelcomeComponent } from './welcome.component';
import { SelectRoleComponent } from './select-role.component';
import { ContactComponent } from './contact.component';
import { OfficeHoursComponent } from './officehours.component';

import { ContactService } from './models.service';
import { OfficeHoursService } from './models.service';
//import { TeacherDetailComponent } from './teacher-detail.component';
//import { TeacherComponent } from './teacher.component';
//import { TeacherService } from './models.service';


@NgModule({
    imports:      [
        BrowserModule,
        FormsModule,
        HttpModule,
        InMemoryWebApiModule.forRoot(InMemoryDataService),
        AppRoutingModule
    ],
    declarations: [
        AppComponent,
        WelcomeComponent,
        SelectRoleComponent,
        ContactComponent,
        OfficeHoursComponent,
        //TeacherDetailComponent,
        //TeacherComponent
    ],
    providers: [ ContactService, OfficeHoursService ],
    bootstrap: [ AppComponent ]
})

export class AppModule { }

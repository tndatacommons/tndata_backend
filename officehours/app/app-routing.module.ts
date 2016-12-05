import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { WelcomeComponent } from './welcome.component';
import { SelectRoleComponent } from './select-role.component';
import { ContactComponent } from './contact.component';
import { OfficeHoursComponent } from './officehours.component';
//import { TeacherDetailComponent } from './teacher-detail.component';
//import { TeacherDetailComponent } from './teacher-detail.component';

const routes: Routes = [
    { path: '', redirectTo: '/welcome', pathMatch: 'full' },
    { path: 'welcome', component: WelcomeComponent },
    { path: 'select-role', component: SelectRoleComponent },
    { path: 'contact', component: ContactComponent },
    { path: 'officehours', component: OfficeHoursComponent },
    //{ path: 'detail/:id', component: TeacherDetailComponent },
    //{ path: 'teacher', component: TeacherComponent }
];

@NgModule({
    imports: [ RouterModule.forRoot(routes) ],
    exports: [ RouterModule ]
})

export class AppRoutingModule {}

export class Contact {
    id: number;
    name: string;
    email: string;
    phone: string;
}

export class OfficeHours {
    id: number;
    fromTime: string;
    toTime: string;
    //days: String[];

    //constructor(fromTime: String, toTime: String) {
        //this.fromTime = fromTime.trim();
        //this.toTime = toTime.trim();
        //console.log("Creatd OfficeHours object with: " + fromTime + ", " + toTime);
    //}

    //addDay(day: String) {
        //this.days.push(day);
        //console.log("Days: ", this.days);
    //}
}


/*
export class Course {
    id: number;
    name: string;
    time: string;
    location: string;
    days: string[];
    code: string[];
    teacherId: number;
    teacherName: string;
}
*/

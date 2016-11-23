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
    days: string[];
    // TODO: need user id or contact id?
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

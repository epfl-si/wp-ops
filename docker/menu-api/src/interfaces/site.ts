import { Tag } from "./tag"
import {Professor} from "./professor";

export interface Site {
    _id: string,
    url: string,
    tagline: string,
    title: string,
    openshiftEnv: string,
    theme: string,
    languages: string[],
    unitId: string,
    snowNumber: string,
    comment: string,
    createdDate: string,
    tags: Tag[],
    userExperience: boolean,
    slug: string,
    professors: Professor[],
    unitName: string,
    unitNameLevel2: string,
    wpInfra: boolean,
    userExperienceUniqueLabel: string,
    categories: string[],
    isDeleted: boolean,
    ansibleHost: string
}

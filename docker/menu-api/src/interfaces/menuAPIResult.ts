import { WpMenu } from './wpMenu'
import {Subscribe} from './subscribe'
import {HrefForSubscribe} from "./hrefForSubscribe";

export interface MenuAPIResult {
    status: string,
    items: WpMenu[],
    _links: Subscribe
}

export class ErrorResult implements MenuAPIResult{
    _links: Subscribe;
    items: WpMenu[];
    status: string;

    constructor(error: string) {
        this._links = {} as Subscribe ;
        this.items = [];
        this.status = error;
    }
}

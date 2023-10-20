import { Site } from "./interfaces/site";
import { MenuAPIResult, ErrorResult } from './interfaces/menuAPIResult'
import {WpMenu} from "./interfaces/wpMenu";
import express, { Request, Response } from 'express';
import {SiteTree, SiteTreeInstance} from "./interfaces/siteTree";

const app = express()
const port = 3000

const headers: Headers = new Headers();
headers.set('Content-Type', 'application/json');
headers.set('Accept', 'application/json');

let openshiftEnv: string[] = [];
let wpVeritasURL: string = '';
let baseUrl: string = '';
const restUrlEnd: string = 'wp-json/epfl/v1/menus/top?lang=en';

let dev = true;
if(dev) {
    openshiftEnv = ["rmaggi"];
    wpVeritasURL = 'https://wp-veritas-test.epfl.ch/api/v1/sites';
    baseUrl = 'https://wp-httpd'
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
}else{
    openshiftEnv = ["labs", "www"];
    wpVeritasURL = 'https://wp-veritas.epfl.ch/api/v1/sites';
    baseUrl = 'https://www.epfl.ch'
}

let arrayMenus: { urlInstanceRestUrl: string, entries: WpMenu[] }[] = [];

function getSiteListFromWPVeritas(): Promise<Site[]> {
    const request: RequestInfo = new Request(wpVeritasURL, {
        method: 'GET',
        headers: headers
    });

    return fetch(request).then(res => res.json()).then(res => {
        return res as Site[];
    });
}

function getMenuForSite(siteURL: string): Promise<MenuAPIResult> {
    if (dev){
        siteURL = siteURL.replace(".epfl.ch","");
    }
    const siteMenuURL: string = siteURL.concat(restUrlEnd);
    const request: RequestInfo = new Request(siteMenuURL, {
        method: 'GET',
        headers: headers
    });

    const timeoutPromise = new Promise<MenuAPIResult>(resolve => {
        setTimeout(resolve.bind(null, new ErrorResult(siteMenuURL.concat(" - Timeout 10s"))), 10000);
    });

    return Promise.race([
        fetch(request).then((res) => res.json()).then((res) => res as MenuAPIResult),
        timeoutPromise
    ]).then((result) => {
        arrayMenus.push( { urlInstanceRestUrl: siteMenuURL.substring(baseUrl.length), entries: result.items } );
        return result;
    }).catch ((error) => {
        let message: string = '';
        if (typeof error === "string") {
            message = error;
        } else if (error instanceof Error) {
            message = error.message;
        }
        return new ErrorResult(siteMenuURL.concat(" - ").concat(message));
    });
}

async function parallel(sites: Site[], fn: (siteURL: string) => Promise<MenuAPIResult>, threads = 10): Promise<MenuAPIResult[]> {
    const result: MenuAPIResult[][] = [];
    while (sites.length) {
        let subListOfSitesMenus: Promise<MenuAPIResult>[] = sites.splice(0, threads).map(x => fn(x.url));
        const res: MenuAPIResult[] = await Promise.all(subListOfSitesMenus);
        result.push(res);
    }
    return result.flat();
}

const searchAllParentsEntriesByID = (entry: WpMenu, urlInstanceRestUrl: string, siteArray: SiteTreeInstance): WpMenu[] => {
    const parent: { [urlInstance : string]: WpMenu } | undefined = siteArray.getParent(urlInstanceRestUrl,entry.ID);
    if (parent) {
        const newUrl = Object.keys(parent)[0];
        if (parent[newUrl]) {
            const parents: WpMenu[] = searchAllParentsEntriesByID(parent[newUrl], newUrl , siteArray);
            return [...parents, parent[newUrl]];
        }else {
            return [];
        }
    } else {
        return [];
    }
}

function refreshMenus() {
    getSiteListFromWPVeritas().then(async sites => {
        const filteredListOfSites: Site[] = sites.filter(function (site){
            return openshiftEnv.includes(site.openshiftEnv);
        });
        await parallel(filteredListOfSites, getMenuForSite, 10);
    });
}

app.get('/refreshMenus', (req, res) => {
    refreshMenus();
    res.send('Menu list charged');
});

app.get('/breadcrumb', (req, res) => {
    const url: string = req.query.url as string;
    const lang: string = req.query.lang as string;

    let breadcrumbForURL: WpMenu[] = [];
    let brothers: WpMenu[] = [];

    const siteArray: SiteTreeInstance = SiteTree(arrayMenus);
    let firstSite: { [urlInstance: string]: WpMenu } | undefined = siteArray.findItemByUrl(url);
    if (firstSite) {
        const restUrl = Object.keys(firstSite)[0];
        if (firstSite[restUrl]) {
            breadcrumbForURL = firstSite !== undefined ? [
                ...searchAllParentsEntriesByID(firstSite[restUrl], restUrl, siteArray),
            ] : [];
            brothers = siteArray.getBrothersAndSisters(restUrl,firstSite[restUrl].ID)
        }
    }

    res.json({
        status: "OK",
        breadcrumb: breadcrumbForURL,
        brothers: brothers
    })
});

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});

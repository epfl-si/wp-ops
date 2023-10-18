import {WpMenu} from "./wpMenu";
import {MenuAPIResult} from "./menuAPIResult";

export type SiteTreeConstructor = (menus : { siteBaseUrl: string, entries: WpMenu[] }[]) => SiteTreeInstance

export interface SiteTreeInstance  {
    getParent : (idParent: number) => WpMenu | undefined
    getChildren : (idParent: number) => WpMenu[]
}

export const SiteTree : SiteTreeConstructor = function(menus) {
    const itemsArray= menus.flatMap((m) => m.entries);
    const itemsByID : { [id : number] : WpMenu }= {};
    itemsArray.forEach(item => {
        itemsByID[item.ID] = item
    });

    const parents: { [id : number] : WpMenu } = {};
    itemsArray.forEach(item => {
        parents[item.ID] = itemsByID[item.menu_item_parent]
    });

    const children: { [id : number] : WpMenu[] } = {};
    itemsArray.forEach(item => {
        if (!children[item.menu_item_parent]) {
            children[item.menu_item_parent] = []
        }

        children[item.menu_item_parent].push(item);
    })

    return {
        getParent(id:number) {
            return parents[id];
        },
        getChildren(id:number) {
            return children[id] || [];
        }
    }
}

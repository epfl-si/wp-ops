import 'mocha';
import { assert } from "chai";
import {SiteTree} from "../src/interfaces/siteTree";
import {WpMenu} from "../src/interfaces/wpMenu";
import * as fs from 'fs';
import {MenuAPIResult} from "../src/interfaces/menuAPIResult";

const bogusWpMenu = {
    post_status: "post_status",
    post_name: "4444",
    post_parent: 5555,
    guid: "aaa-2-bbbb",
    menu_order:1,
    post_type: "post",
    db_id: 12345,
    object_id: 67890,
    object: "page",
    type_label: "Page",
    url: "http://toto.com/some/page"
}

const bogusExternalWpMenu = {
    post_status:"publish",
    post_name:"19761",
    post_parent:0,
    menu_order:2,
    post_type:"nav_menu_item",
    db_id:19761,
    object:"epfl-external-menu",
    type_label:"External Menu"
}

describe("Site Tree", function() {
    describe("in a single site", function() {
        it("has a parent", function() {
            const parent : WpMenu = {ID: 1, menu_item_parent: 0, title: "Some_Page parent 1",rest_url: "http://toto.com/wp-json/bla?bla", ...bogusWpMenu},
                child : WpMenu = {ID: 2, menu_item_parent: 1, title: "Some_Page child 1",rest_url: "http://toto.com/wp-json/bla?bla", ...bogusWpMenu};
            const siteTree = SiteTree([{ urlInstanceRestUrl: "http://toto.com/wp-json/bla?bla", entries: [parent, child] }]);
            const tree = siteTree.getParent("http://toto.com/wp-json/bla?bla",2);
            if (tree) {
                assert(tree["http://toto.com/wp-json/bla?bla"].ID === 1);
            } else {
                assert.fail();
            }
        })
        it("has a child", function() {
            const parent : WpMenu = {ID: 1, menu_item_parent: 0, title: "Some_Page parent 1", rest_url: "http://toto.com/wp-json/bla?bla",...bogusWpMenu},
                child : WpMenu = {ID: 2, menu_item_parent: 1, title: "Some_Page child 1",rest_url: "http://toto.com/wp-json/bla?bla", ...bogusWpMenu};
            const siteTree = SiteTree([{ urlInstanceRestUrl: "https://toto.com/wp-json/bla?bla", entries: [parent, child] }]);
            assert.deepEqual(siteTree.getChildren("https://toto.com/wp-json/bla?bla",1), [child])
        })
        it("doesn't crash when parentID points nowhere", function() {
            const parent : WpMenu = {ID: 1, menu_item_parent: 0, title: "Some_Page parent 1", rest_url: "http://toto.com/wp-json/bla?bla",...bogusWpMenu},
                child : WpMenu = {ID: 2, menu_item_parent: 3, title: "Some_Page child 1",rest_url: "http://toto.com/wp-json/bla?bla",  ...bogusWpMenu};
            const siteTree = SiteTree([{ urlInstanceRestUrl: "https://toto.com/wp-json/bla?bla", entries: [parent, child] }]);
            const tree1 = siteTree.getParent("https://toto.com/wp-json/bla?bla",2);
            if (tree1) {
                assert(tree1["http://toto.com/wp-json/bla?bla"] === undefined);
            } else {
                assert.fail();
            }
            assert.deepEqual(siteTree.getChildren("https://toto.com/wp-json/bla?bla",1), []);
        })
    })
    describe("in multiple sites", function() {
        /*it("doesn't crach with multiple sites", function() {
            const parent : WpMenu = {ID: 1, menu_item_parent: 0, title: "Some_Page parent 1", ...bogusWpMenu},
                child : WpMenu = {ID: 2, menu_item_parent: 1, title: "Some_Page child 2", ...bogusWpMenu};
            const parent2 : WpMenu = {ID: 1, menu_item_parent: 0, title: "Some_Page parent 1 bis", ...bogusWpMenu},
                child2 : WpMenu = {ID: 3, menu_item_parent: 1 ,title: "Some_Page child 3", ...bogusWpMenu};
            const siteTree = SiteTree([{ siteBaseUrl: "https://toto.com", entries: [parent, child] },{ siteBaseUrl: "https://tototata.com", entries: [parent2, child2] }]);
            assert(siteTree.getParent(2)?.title === "Some_Page parent 1");
            assert(siteTree.getParent(3)?.title === "Some_Page parent 1 bis");
        })*/
        it("doesn't crach with multiple sites", function() {
            const parent : WpMenu = {ID: 1, menu_item_parent: 0, title: "Some_Page parent 1",rest_url: "http://toto.com/wp-json/bla?bla", ...bogusWpMenu},
                child : WpMenu = {ID: 2, menu_item_parent: 1, title: "Some_Page child 2",rest_url: "http://toto.com/wp-json/bla?bla", ...bogusWpMenu};
            const parent2 : WpMenu = {ID: 1, menu_item_parent: 0, title: "Some_Page parent 1 bis",rest_url: "http://tototata.com/wp-json/bla?bla", ...bogusWpMenu},
                child2 : WpMenu = {ID: 3, menu_item_parent: 1 ,title: "Some_Page child 3",rest_url: "http://tototata.com/wp-json/bla?bla", ...bogusWpMenu};
            const siteTree = SiteTree([{ urlInstanceRestUrl: "https://toto.com/wp-json/bla?bla", entries: [parent, child] },{ urlInstanceRestUrl: "https://tototata.com/wp-json/bla?bla", entries: [parent2, child2] }]);
            const tree1 = siteTree.getParent("https://toto.com/wp-json/bla?bla", 2);
            const tree2 = siteTree.getParent("https://tototata.com/wp-json/bla?bla", 3);
            if (tree1) {
                assert(tree1["https://toto.com/wp-json/bla?bla"].title === "Some_Page parent 1");
            } else {
                assert.fail();
            }
            if (tree2) {
                assert(tree2["https://tototata.com/wp-json/bla?bla"].title === "Some_Page parent 1 bis");
            } else {
                assert.fail();
            }
        })
        it("gets external site reference", function() {
            const parent : WpMenu = {ID: 1, menu_item_parent: 0, title: "Some_Page parent 1",rest_url: "http://tototata.com/wp-json/bla?bla", ...bogusWpMenu},
                child : WpMenu = {ID: 2, menu_item_parent: 1, title: "Some_Page child 2",rest_url: "http://tototata.com/wp-json/bla?bla", ...bogusWpMenu},
                parent2 : WpMenu = {ID: 1, menu_item_parent: 0, title: "Some_Page parent 1 bis",rest_url: "http://tototata.com/wp-json/bla?bla", ...bogusWpMenu},
                child2 : WpMenu = {ID: 3, menu_item_parent: 1 ,title: "Some_Page child 3",rest_url: "http://tototata.com/wp-json/bla?bla", ...bogusWpMenu},
                child3 : WpMenu = {ID: 4, menu_item_parent: 1, title: "Some_Page external menu 4", rest_url:"https://toto.com/wp-json/bla?bla", ...bogusExternalWpMenu};
            const siteTree = SiteTree([{ urlInstanceRestUrl: "https://toto.com/wp-json/bla?bla", entries: [parent, child] },
                { urlInstanceRestUrl: "https://tototata.com/wp-json/bla?bla", entries: [parent2, child2, child3] }]);
            assert(siteTree.findExternalMenuByRestUrl(child3.rest_url!)?.title=="Some_Page parent 1");
        })
        it("gets the correct instance parent in a different instance", function() {
            const jsonService =  fs.readFileSync('./test/data/services.json', 'utf-8');
            const jsonWebSite =  fs.readFileSync('./test/data/website.json', 'utf-8');
            const serviceMenu: MenuAPIResult = JSON.parse(jsonService);
            const websiteMenu: MenuAPIResult = JSON.parse(jsonWebSite);
            const siteTree = SiteTree([{ urlInstanceRestUrl: "/campus/services/wp-json/epfl/v1/menus/top?lang=en", entries: serviceMenu.items },
                { urlInstanceRestUrl: "/campus/services/website/wp-json/epfl/v1/menus/top?lang=en", entries: websiteMenu.items }]);
            const tree1 = siteTree.getParent("/campus/services/website/wp-json/epfl/v1/menus/top?lang=en", 15624);
            if (tree1) {
                assert(tree1["/campus/services/wp-json/epfl/v1/menus/top?lang=en"].ID === 7119);
            } else {
                assert.fail();
            }
        })
        it("gets the correct instance child", function() {
            const jsonCampus =  fs.readFileSync('./test/data/services.json', 'utf-8');
            const jsonWebSite =  fs.readFileSync('./test/data/website.json', 'utf-8');
            const campusMenu: MenuAPIResult = JSON.parse(jsonCampus);
            const websiteMenu: MenuAPIResult = JSON.parse(jsonWebSite);
            const siteTree = SiteTree([{ urlInstanceRestUrl: "/campus/services/wp-json/epfl/v1/menus/top?lang=en", entries: campusMenu.items },
                { urlInstanceRestUrl: "/campus/services/website/wp-json/epfl/v1/menus/top?lang=en", entries: websiteMenu.items }]);
            const children = siteTree.getChildren("/campus/services/wp-json/epfl/v1/menus/top?lang=en", 7119);
            assert(children.filter(item => item.ID ===15624 ).length == 1);
        })
    })
});
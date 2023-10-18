import 'mocha';
import assert from "assert";
import {SiteTree} from "../src/interfaces/siteTree";
import {WpMenu} from "../src/interfaces/wpMenu";

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
    url: "http://toto.com/some/page",
    title: "Some_Page",
    rest_url: "http://toto.com/wp-json/bla?bla"

}
describe("Site Tree", function() {
    describe("in a single site", function() {
        it("has a parent", function() {
            const parent : WpMenu = {ID: 1, menu_item_parent: 0, ...bogusWpMenu},
                child : WpMenu = {ID: 2, menu_item_parent: 1, ...bogusWpMenu};
            const siteTree = SiteTree([{ siteBaseUrl: "https://toto.com", entries: [parent, child] }]);
            assert(siteTree.getParent(2)?.ID === 1);
        })
        it("has a child", function() {
            const parent : WpMenu = {ID: 1, menu_item_parent: 0, ...bogusWpMenu},
                child : WpMenu = {ID: 2, menu_item_parent: 1, ...bogusWpMenu};
            const siteTree = SiteTree([{ siteBaseUrl: "https://toto.com", entries: [parent, child] }]);
            assert
        })
    })
});
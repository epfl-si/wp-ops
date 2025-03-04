"use strict";
var url = require('url');

let namespace = "svc0041p-wordpress"; // svc0041t-wordpress
let hostname = "www.epfl.ch";

// Function to fetch and filter the data
async function fetchAndFilterSites() {
  try {
    // Fetch data from the API
    const response = await fetch('https://wp-veritas.epfl.ch/api/v1/sites');
    const data = await response.json();
    // filter on "www"
    let filteredSites = data;
    filteredSites = filteredSites.filter(site => site.openshiftEnv == 'www' && site.wpInfra);
    // without the WPForms plugin
    filteredSites = filteredSites.filter(site => !site.categories.includes('WPForms'))
    filteredSites = filteredSites.filter(site => site.ansibleHost.indexOf("www__about") > -1);

    filteredSites.sort((a, b) => b.url.length - a.url.length);
    return filteredSites;
  } catch (error) {
    console.error('Error fetching or filtering sites:', error);
  }
}

const determinePlugins = (categories, openshiftEnv) => {
  return JSON.stringify(categories || [])
}

const getName = (ansibleHost) => {
  let name = ansibleHost.replaceAll("__","-").replaceAll("_", "-");
  let index = 1;
  while (name.length >= 50) {
    name = name.split("-").slice(0, index).map(e => e[0]).concat(name.split("-").slice(index)).join("-");
    index++;
  }
  return name;
}

const run = async () => {
  // Call the function
  let sites = await fetchAndFilterSites();
  for (const site of sites) {
    let path = site.url.replace(/https:\/\/.*?\.epfl\.ch/, '');
    path = path.replace(/\/$/, "");  // Removes the trailing slash

    const siteYml = `apiVersion: wordpress.epfl.ch/v1
kind: WordpressSite
metadata:
  name: ${getName(site.ansibleHost)}
  namespace: ${namespace}
spec:
  hostname: ${hostname}
  path: ${path}
  owner:
    epfl:
      unitId: ${site.unitId}
  wordpress:
    title: ${site.title}
    tagline: ${site.tagline}
    theme: wp-theme-2018
    languages: ${JSON.stringify(site.languages || [] )}
    plugins: ${determinePlugins(site.categories, site.openshiftEnv)}
    debug: ${namespace=='svc0041p-wordpress' ? false : true}
  epfl:
    import:
      sourceType: openshift3
      openshift3BackupSource:
        environment: ${site.openshiftEnv}
        ansibleHost: ${site.ansibleHost}
`
      console.log(siteYml);
      console.log('---');
  }
}

run()

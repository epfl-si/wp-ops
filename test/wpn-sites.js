"use strict";
var url = require('url');

let namespace = "svc0041p-wordpress"; // svc0041t-wordpress

// Function to fetch and filter the data
async function fetchAndFilterSites() {
  try {
    // Fetch data from the API
    const response = await fetch('https://wp-veritas.epfl.ch/api/v1/sites');
    const data = await response.json();

    // Filter the sites where openshiftEnv is "www" or "labs"
    // let filteredSites = data.filter(site => site.openshiftEnv !== '');
    
    // filter on "labs"
    let filteredSites = data.filter(site => site.openshiftEnv === 'labs');
    // without the WPForms plugin
    filteredSites = filteredSites.filter(site => !site.categories.includes('WPForms'))
    return filteredSites;
  } catch (error) {
    console.error('Error fetching or filtering sites:', error);
  }
}

const determinePlugins = (categories, openshiftEnv) => {
  if (['www'].indexOf(openshiftEnv) > -1) {
    categories.push('epfl-menus');
  }
  return JSON.stringify(categories || [])
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
  name: ${site.ansibleHost.replaceAll("__","-").replaceAll("_", "-")}
  namespace: ${namespace}
spec:
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

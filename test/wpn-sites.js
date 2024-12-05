"use strict";
var url = require('url');

let namespace = "wordpress-test";

// Function to fetch and filter the data
async function fetchAndFilterSites() {
  try {
    // Fetch data from the API
    const response = await fetch('https://wp-veritas.epfl.ch/api/v1/sites');
    const data = await response.json();

    // Filter the sites where openshiftEnv is "www" or "labs"
    let filteredSites = data.filter(site => site.openshiftEnv !== '');
    return filteredSites;
  } catch (error) {
    console.error('Error fetching or filtering sites:', error);
  }
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
  visibility: public
  kubernetes:
    service: test
  wordpress:
    title: ${site.title}
    tagline: ${site.tagline}
    theme: wp-theme-2018
    languages:
${site.languages.map(item => `      - ${item}`).join('\n')}
    plugins:
${site.categories.map(item => `      - ${item}`).join('\n')}
    debug: true
  epfl:
    unit_id: ${site.unitId}
    unit_name: ${site.unitName}
    importFromOS3:
      environment: ${site.openshiftEnv}
      ansibleHost: ${site.ansibleHost}
`
    console.log(siteYml);
    console.log('---');
  }
}

run()

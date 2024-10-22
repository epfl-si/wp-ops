"use strict";

// Function to fetch and filter the data
async function fetchAndFilterSites() {
  try {
    // Fetch data from the API
    const response = await fetch('https://wp-veritas.epfl.ch/api/v1/sites');
    const data = await response.json();

    // Filter the sites where openshiftEnv is "www"
    let filteredSites = data.filter(site => site.openshiftEnv === 'www' || site.openshiftEnv === 'labs');

    // Filter the sites that are not www.epfl.ch
    filteredSites = filteredSites.filter(site => site.url.includes('https://www.epfl.ch'));

    // Filter the sites that are an association
    // filteredSites = filteredSites.filter(site => !site.url.includes('campus/associations/list'));

    // Log or return the filtered data
    //console.log(filteredSites);
    //console.log(filteredSites.length);
    return filteredSites;
  } catch (error) {
    console.error('Error fetching or filtering sites:', error);
  }
}


const run = async () => {
  // Call the function
  let sites = await fetchAndFilterSites();
  // console.log(sites)
  for (const site of sites) {
    //console.log(site);
    let path = site.url.replace("https://www.epfl.ch", "")
    path = path.replace(/\/$/, "");  // Removes the trailing slash

    const siteYml = `apiVersion: wordpress.epfl.ch/v1
kind: WordpressSite
metadata:
  name: ${site.ansibleHost.replaceAll("__","-").replaceAll("_", "-")}
  namespace: wordpress-test
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
    debug: true
  epfl:
    unit_id: ${site.unitId}
`
    console.log(siteYml);
    console.log('---');
  }
}

run()

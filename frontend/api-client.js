const BASE_URL = `/api`

class APIClient {

  getProjects() {
    const headers = new Headers({
      "Content-type": "application/json"
    });
    const url = BASE_URL + `/projects`
    return fetch(url, {
      method: 'GET',
      headers: headers
    })
  }

  getPages(project, mode) {
    const headers = new Headers({
      "Content-type": "application/json"
    });
    const url = BASE_URL + `/pages?project=${project}&algorithm=${mode}`
    return fetch(url, {
      method: 'GET',
      headers: headers
    })
  }

  search(query, project, mode) {
    const headers = new Headers({
      "Content-type": "application/json"
    });
    const url = BASE_URL + `/search?project=${project}&q=${query}&algorithm=${mode}`
    return fetch(url, {
      method: 'GET',
      headers: headers
    })
  }
  
  facetedSearch(facets, query, project, mode) {
    const headers = new Headers({
      "Content-type": "application/json"
    });
    let url = BASE_URL + `/search/facet?project=${project}&facets=${facets}&algorithm=${mode}`
    if (query) {
      url = url + `&q=${query}`
    }
    return fetch(url, {
      method: 'GET',
      headers: headers
    })
  }

}

module.exports = new APIClient()
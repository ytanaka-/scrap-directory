<template>
  <div class="wrap">
    <div id="search">
      <div id="menu-bar">
        <div class="system-name" @click="clear();"><span>ScrapDirectory</span></div>
        <div class="menu-bar-container">
          <input type="text" id="query" v-model="query" @keydown.enter="clickSearch()">
          <button @click="clickSearch();">検索</button>
        </div>
        <v-select class="select-algorithm" :options="algorithms" v-bind:value="selectedAlgorithm" @input="setSelectedAlgorithm" :clearable="false"></v-select>
        <v-select class="select-project" :options="projects" v-bind:value="selectedProject" @input="setSelectedProject" :clearable="false"></v-select>
      </div>
    </div>
    <div id="main">
      <div id="facet-bar">
        <div class="facet-list-title">ファセット一覧</div>
        <div class="facet-list">
          <template v-for="(directory,i) in directories">
            <div v-if="directory.facets.length > 0" class="facet-list-wrap" v-bind:key="i">
              <div class="facet-list-container">
                <template v-for="(facet) in directory.facets">
                  <div class="facet" @click="clickFacet(facet,i);" v-bind:key="facet.name" v-bind:class="{ focus: facet.focus }">
                    <div class="facet-text">{{facet.name}}</div>
                    <template v-if="facet.neighbors_size < FACET_THRESHOLD">
                      <div class="facet-neighbors-size"><span>{{facet.neighbors_size}}</span></div>
                    </template>
                    <template v-else>
                      <div class="facet-neighbors-size"><img src="img/baseline_play_arrow_black_48dp.png"/></div>
                    </template>
                  </div>
                </template>
              </div>
            </div>
          </template>
        </div>
      </div>
      <div id="list" ref="list">
        <div class="list-wrap">
          <div class="list-top-title">すべてのページ {{pageListMessage}}</div>
          <template v-for="(page) in currentPages">
            <div class="list-container" v-bind:key="page.id">
              <div class="text-box">
                <div class="title">
                  <a v-bind:href="page.url" target="_blank" rel="noopener">
                    <span>{{page.title}}</span>
                  </a>
                </div>
              </div>
              <div class="description">
                <div class="description-text">{{page.description}}</div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import APIClient from '../api-client'

export default {
  name: 'Main',
  
  data: () => ({
    selectedProject: "",
    projects: [],
    selectedAlgorithm: "InDegree",
    algorithms: ["InDegree","InDegree-MMR","PageRank"],
    query: "",
    directories: [],
    FACET_THRESHOLD: 5,
    pageListMessage: ""
  }),

  computed: {
    currentPages: function(){
      const directories = this.directories
      if(directories.length > 0){
        return directories[directories.length - 1].pages
      } else {
        return []
      }
    }
  },

  created() {
    APIClient.getProjects().then(res => res.json())
    .then((data) => {
      const projects = data.projects
      for (let i = 0;i < projects.length;i++){
        if (i == 0) {
          this.selectedProject = projects[i].name
        }
        this.projects.push(projects[i].name)
      }
      this.initPages()
    }).catch((err) => {
      console.log(err)
    })
  },

  methods: {
    initPages: function(){
      this.query = ""
      this.directories = []
      this.pageListMessage = ""
      APIClient.getPages(this.selectedProject, this.selectedAlgorithm).then(res => res.json())
      .then((data) => {
        this.directories.push({
          pages: data.pages,
          facets: data.facets,
          query: ""
        })
      }).catch((err) => {
        console.log(err)
      })
    },

    search: function(query){
      APIClient.search(query, this.selectedProject, this.selectedAlgorithm).then(res => res.json())
      .then((data) => {
        this.directories.push({
          pages: data.pages,
          facets: data.facets,
          query: query
        })
      }).catch((err) => {
        console.log(err)
      })
    },

    facetedSearch: function(facetsQuery, query, isNextFacet=true){
      APIClient.facetedSearch(facetsQuery, query, this.selectedProject, this.selectedAlgorithm).then(res => res.json())
      .then((data) => {
        if (isNextFacet) {
          this.directories.push({
            pages: data.pages,
            facets: data.facets,
            query: facetsQuery
          })
        } else {
          this.directories.push({
            pages: data.pages,
            facets: [],
            query: facetsQuery
          })
        }
      }).catch((err) => {
        console.log(err)
      })
    },
    
    clear: function() {
      this.initPages()
    },

    clickSearch: function() {
      // 日本語入力中のEnterキー操作は無効にする
      if (event.keyCode !== 13) return
      this.directories = []
      this.pageListMessage = ""
      this.search(this.query)
    },

    setSelectedProject: function(project) {
      this.selectedProject = project
      this.initPages()
    },

    setSelectedAlgorithm: function(algorithm) {
      this.selectedAlgorithm = algorithm
      this.initPages()
    },

    clickFacet: function(selectedFacet, directoryLevel) {
      let isClear = true
      let current = this.directories[directoryLevel]
      for (let cFacet of current.facets){
        if (cFacet.name == selectedFacet.name) {
          if (selectedFacet.focus == undefined || selectedFacet.focus == false) {
            selectedFacet.focus = true
            isClear = false
          } else {
            selectedFacet.focus = false
          }
        } else {
          cFacet.focus = false
        }
      }
      let facetsQuery = ""
      if (isClear) {
        const removeNum = this.directories.length - directoryLevel - 1
        this.directories.splice(directoryLevel+1, removeNum)
        if (directoryLevel > 0) {
          facetsQuery =  this.directories[directoryLevel-1].query
        }
        // この辺の文言全部Computedで肩代わりした方がよい
        let searchMessage = facetsQuery.split(" ").join("> ")
        searchMessage = searchMessage.replace(">","")
        if (facetsQuery == "") {
          this.pageListMessage = ""
        }else{
          this.pageListMessage = `>${searchMessage}`
        }
      } else {
        // 最下層でない場合は選択された階層を基点にする
        if (this.directories.length > directoryLevel) {
          const removeNum = this.directories.length - directoryLevel - 1
          this.directories.splice(directoryLevel+1, removeNum)
        }
        if (directoryLevel > 0) {
          facetsQuery =  this.directories[directoryLevel].query
        }
        if (facetsQuery != ""){
          facetsQuery = facetsQuery + " " + selectedFacet.name
        } else {
          facetsQuery = selectedFacet.name
        }
        let isNextFacet = true
        if (selectedFacet.neighbors_size < this.FACET_THRESHOLD) {
          isNextFacet = false
        }
        if (this.query != "") {
          this.facetedSearch(facetsQuery, this.query, isNextFacet)
        } else {
          this.facetedSearch(facetsQuery, null, isNextFacet)
        }
        
        let searchMessage = facetsQuery.split(" ").join("> ")
        this.pageListMessage = `>${searchMessage}`
      }
    }
  }
}
</script>

<style lang="stylus">

#search {
  padding: 7px;
  height: 36px;
  width: 100%;
  background-color: #222;
  color: #959595;
  white-space: nowrap;
}

#menu-bar {
  height: 100%;
  width: 100%;
  display: flex;
}

.system-name {
  height: 100%;
  width: 240px;
  font-size: 24px;
  color: #FFF;
  margin-left: 10px;
}

.system-name span {
  line-height: 36px;
  cursor: pointer;
}

.menu-bar-container {
  height: 100%;
  margin-top: 2px;
  margin-right: auto;
}

.menu-bar-container #query {
  min-width: 500px;
  height: 22px;
  font-size: 14px;
  padding: 4px;
  border-radius: 5px;
  border: 1px solid #ccc
  background-image: url("/img/baseline_search_black_48dp.png");
  background-repeat: no-repeat;
  background-size: contain;
  padding-left: 30px;
}

.menu-bar-container button {
  font-size: 14px;
  height: 28px;
  margin: 0px 4px;
  padding: 2px 8px;
}

.select-algorithm {
  width: 160px;
  margin-top: 0px;
  margin-right: 20px;
}

.select-project {
  width: 200px;
  margin-top: 0px;
  margin-right: 30px;
}

.vs--searchable .vs__dropdown-toggle {
  background-color: #FFF;
}

#main {
  display: flex;
  width: 100%;
}

.focus {
  background: #888;
}

#facet-bar {
  min-width: 202px;
  margin-right: 10px;
  padding: 5px 10px;
  padding-left: 15px;
  position: relative;
  background-color: #f5f5f5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.facet-list {
  display: flex;
  padding-right: 15px;
}


.facet-list-wrap {
  height: 100vh;
  border-right: 1px solid #AAA;
  overflow-y: scroll;
}

.facet-list-container {
  width: 180px;
  padding-right: 6px;
}

.facet-list-title {
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid #AAA;
  padding-bottom: 3px;
}

.facet {
  width: 100%;
  height: 23px;
  padding-top: 5px;
  padding-bottom: 5px;
  padding-left: 3px;
  padding-right: 3px;
  display: flex;
}

.facet-text {
  width: 100%;
  font-size: 15px;
  margin-left: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.facet-neighbors-size {
  font-size: 15px;
  margin-top: 2px;
  margin-right: 5px;
  margin-left: auto;
  padding-left: 2px;
}

.facet-neighbors-size span {
  padding-right: 4px;
}

.facet-neighbors-size img {
  height: 18px;
  width: 18px;
}


a {
  color: #1C5D99;
  font-weight: bold;
  font-size: 17px;
   word-wrap: break-word;
  text-decoration: none;
}
a:visited {
  color: #6E97BE;
  text-decoration: none;
}
a:hover, a:focus {
  text-decoration: underline;
}


#list {
  overflow: scroll;
  margin-left: 5px;
  height: 100vh;
  flex: 1;
}

.list-wrap {
  max-width: 1000px;
  margin-left: 5px
  margin-right: 20px;
}

.list-top-title {
  font-size: 16px;
  font-weight: bold;
  padding-top: 5px;
  padding-bottom: 3px;
  border-bottom: 1px solid #AAA;
}

.list-container {
  width: 100%;
  min-height: 74px;
  padding: 10px 2px;
  padding-bottom: 7px;
  border-bottom: 1px solid #e0e0e0;
}

.description {
  margin-top: 9px;
  margin-right: 6px;
  margin-bottom: 4px;
}

.description-text {
  font-size: 13px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  color: #222;
}

</style>
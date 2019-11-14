import Vue from 'vue';
import App from './components/app.vue';
import vSelect from 'vue-select';
import 'vue-select/dist/vue-select.css';
Vue.component('v-select', vSelect)

const app = new Vue(App).$mount('#app');
import HomeView from "./views/HomeView.vue";
import ChatView from "./views/ChatView.vue";
import UploadView from "./views/UploadView.vue";
import AboutView from "./views/AboutView.vue";

const routes = [
  { path: "/", name: "home", component: HomeView },
  { path: "/loan", name: "loan", component: ChatView },
  { path: "/upload", name: "upload", component: UploadView },
  { path: "/about", name: "about", component: AboutView },
];

export default routes;

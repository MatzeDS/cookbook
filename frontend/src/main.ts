import "./theme/main.css";

import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";

import PrimeVue from "primevue/config";
import { preset } from "./theme/preset";

const app = createApp(App);

app.use(router);

app.use(PrimeVue, {
  theme: {
    preset,
    options: {
      prefix: "cb",
      darkModeSelector: "system",
    },
  },
});

app.mount("#app");

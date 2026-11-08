"use strict";
// Практична робота №2: DOM, події, умови, масиви та localStorage.
document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const themeButton = document.querySelector("#theme-toggle");
  const menuButton = document.querySelector("#menu-toggle");
  const navigation = document.querySelector("#main-nav");
  const savedTheme = localStorage.getItem("portfolio-theme");

  function setTheme(theme) {
    const light = theme === "light";
    body.classList.toggle("light-theme", light);
    themeButton.textContent = light ? "☾ Темна тема" : "☀ Світла тема";
    themeButton.setAttribute("aria-label", light ? "Увімкнути темну тему" : "Увімкнути світлу тему");
    localStorage.setItem("portfolio-theme", theme);
  }
  setTheme(savedTheme === "light" ? "light" : "dark");
  themeButton.addEventListener("click", () => setTheme(body.classList.contains("light-theme") ? "dark" : "light"));

  function closeMenu() {
    navigation.classList.remove("nav-open");
    menuButton.setAttribute("aria-expanded", "false");
    menuButton.textContent = "☰ Меню";
  }
  menuButton.addEventListener("click", () => {
    const open = navigation.classList.toggle("nav-open");
    menuButton.setAttribute("aria-expanded", String(open));
    menuButton.textContent = open ? "✕ Закрити" : "☰ Меню";
  });
  navigation.querySelectorAll("a").forEach(link => link.addEventListener("click", closeMenu));
  window.addEventListener("resize", () => { if (window.innerWidth > 768) closeMenu(); });

  const greetings = [
    "Навчаюся програмуванню та розвиваю навички веброзробки. Мені подобається перетворювати ідеї на зручні, сучасні й адаптивні сайти.",
    "JavaScript робить цю сторінку інтерактивною: натискайте кнопки та досліджуйте можливості!",
    "Кожен новий проєкт — це ще один крок до професійної веброзробки."
  ];
  let greetingIndex = 0;
  document.querySelector("#change-text").addEventListener("click", () => {
    greetingIndex = (greetingIndex + 1) % greetings.length;
    document.querySelector("#hero-description").textContent = greetings[greetingIndex];
  });

  // Масив об'єктів та створення HTML-елементів через DOM.
  const projects = [
    { id: 1, name: "Інтерактивний список завдань" },
    { id: 2, name: "Калькулятор витрат" }
  ];
  let nextId = 3;
  const projectList = document.querySelector("#dynamic-projects");
  const projectInput = document.querySelector("#project-name");
  const projectHint = document.querySelector("#project-hint");
  function renderProjects() {
    projectList.replaceChildren();
    projects.forEach(project => {
      const card = document.createElement("article");
      card.className = "dynamic-card";
      const title = document.createElement("strong");
      title.textContent = project.name;
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "remove-project";
      remove.textContent = "Видалити ×";
      remove.setAttribute("aria-label", `Видалити проєкт ${project.name}`);
      remove.addEventListener("click", () => {
        const index = projects.findIndex(item => item.id === project.id);
        if (index !== -1) projects.splice(index, 1);
        renderProjects();
        projectHint.textContent = "Проєкт видалено.";
      });
      card.append(title, remove);
      projectList.append(card);
    });
  }
  document.querySelector("#add-project").addEventListener("click", () => {
    const name = projectInput.value.trim();
    if (name.length < 3) {
      projectHint.textContent = "Введіть назву проєкту (щонайменше 3 символи).";
      projectInput.focus();
      return;
    }
    projects.push({ id: nextId++, name });
    renderProjects();
    projectInput.value = "";
    projectHint.textContent = "Новий проєкт успішно додано!";
  });
  projectInput.addEventListener("keydown", event => {
    if (event.key === "Enter") { event.preventDefault(); document.querySelector("#add-project").click(); }
  });
  renderProjects();

  // Асинхронна відправка через Fetch API, без перезавантаження.
  const form = document.querySelector("#contact-form");
  const feedback = document.querySelector("#form-feedback");
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const name = form.querySelector("#name").value.trim();
    const email = form.querySelector("#email").value.trim();
    const message = form.querySelector("#message").value.trim();
    feedback.classList.remove("success");
    if (name.length < 2) { feedback.textContent = "Вкажіть ім’я (щонайменше 2 символи)."; return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { feedback.textContent = "Введіть коректний Email."; return; }
    if (message.length < 5) { feedback.textContent = "Повідомлення має містити щонайменше 5 символів."; return; }
    const submit = form.querySelector('[type="submit"]');
    submit.disabled = true;
    feedback.textContent = "Зберігаємо повідомлення...";
    try {
      const response = await fetch("/api/messages", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, message })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Помилка сервера");
      feedback.classList.add("success");
      feedback.textContent = `Дякуємо, ${name}! Повідомлення №${data.id} збережено в базі даних.`;
      form.reset();
    } catch (error) { feedback.textContent = error.message + " Перевірте, чи запущено Python-сервер."; }
    finally { submit.disabled = false; }
  });
});

# FRONTEND TRACK — COMPLETE QUESTION BANK
## Ready for import into the Quiz Question table (Tier 1 / Tier 2a / Tier 2b / Tier 3)

---

## HOW TO IMPORT THIS (READ FIRST, ASTRA)

This is real content for the **Frontend** track only — replace the placeholder/example Frontend questions with this content. Do not touch any other track's questions (Backend is already imported separately), do not restructure the schema, do not add new fields beyond what's already defined in `Question` (Addendum 1) and the tier logic (Addendum 2).

**Same distinction as Backend, preserved exactly:**
`Skill` = the label shown to the student and used for scoring that specific skill dimension.
`Requires Tier-2 flag` = which of the 5 tracked Tier-2a skills triggers this question's eligibility.
These do **not** have to match. Several Tier-3 questions test adjacent skills (Accessibility, Performance, Testing, Forms, TypeScript) while gated behind the closest tracked skill (HTML/CSS, JavaScript, React, or API Integration). **This is intentional clustering, not a data error — do not "correct" it.**

**Pool size vs. served size:** 60 Tier-3 candidates in this file. Engine serves a **maximum of 15** per student, same adaptive selection rules as Backend (prioritize highest Tier-1 self-rated flagged skills, mix project-informed with pure skill-verification questions).

---

## TIER 1 — Confidence / Self-Rating (15 questions, all served to every Frontend-track student)

| # | Skill | Question Text |
|---|---|---|
| 1 | HTML | Rate your HTML proficiency (1–10). |
| 2 | CSS | Rate your CSS proficiency (1–10). |
| 3 | JavaScript | Rate your JavaScript proficiency (1–10). |
| 4 | React | Rate your React proficiency (1–10). |
| 5 | TypeScript | Rate your TypeScript proficiency (1–10). |
| 6 | Responsive Design | Rate your proficiency in building responsive interfaces (1–10). |
| 7 | State Management | Rate your proficiency with frontend state management (1–10). |
| 8 | API Integration | Rate your proficiency in consuming REST APIs from frontend applications (1–10). |
| 9 | Accessibility | Rate your proficiency in building accessible web interfaces (1–10). |
| 10 | Git | Rate your proficiency with Git for frontend development (1–10). |
| 11 | Debugging | Rate your proficiency in debugging frontend applications (1–10). |
| 12 | Performance | Rate your proficiency in improving frontend performance (1–10). |
| 13 | Forms & Validation | Rate your proficiency in implementing frontend forms and validation (1–10). |
| 14 | Testing | Rate your proficiency in frontend testing (1–10). |
| 15 | UI Component Design | Rate your proficiency in creating reusable UI components (1–10). |

---

## TIER 2a — Project Count (5 questions, tracked skills only)

| # | Skill | Question Text |
|---|---|---|
| 1 | HTML/CSS | How many projects or assignments have you completed involving HTML/CSS interface development? |
| 2 | JavaScript | How many projects or assignments have you completed involving JavaScript frontend development? |
| 3 | React | How many projects or assignments have you completed using React? |
| 4 | API Integration | How many projects or assignments have you completed involving frontend API integration? |
| 5 | State Management | How many projects or assignments have you completed involving frontend state management? |

**Routing rule:** 2+ reported experiences flags that skill for Tier 3 eligibility. 0 = no Tier 3 verification for that skill.

---

## TIER 2b — Project Context (5 questions, not correctness-graded — used only for routing/context)

| # | Question |
|---|---|
| 1 | Briefly describe one frontend project you worked on. |
| 2 | How much of the frontend did you build yourself versus with a team? |
| 3 | How much did you rely on AI tools such as ChatGPT or Copilot while building it? |
| 4 | What was the hardest frontend problem you encountered? |
| 5 | How confident are you explaining the structure, components, and technical decisions of that project to someone else? |

---

## TIER 3 — Verification Question Candidate Pool (60 questions, engine selects max 15 per student)

All questions are single-answer MCQ for deterministic auto-grading. No AI/model grades these.

### HTML / CSS / Responsive / Accessibility (13 questions)

**Q1** — Skill: HTML | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> Which HTML element is most appropriate for the primary heading of a page?
> A. `<h1>`  B. `<span>`  C. `<div>`  D. `<label>`
> **Correct: A**

**Q2** — Skill: HTML | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> Which element is intended for a group of navigation links?
> A. `<nav>`  B. `<section>`  C. `<aside>`  D. `<footer>`
> **Correct: A**

**Q3** — Skill: HTML | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> A button performs an action such as submitting a form. Which element is most appropriate?
> A. `<button>`  B. `<div>`  C. `<span>`  D. `<p>`
> **Correct: A**

**Q4** — Skill: HTML | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> What is the main purpose of the `alt` attribute on an informative image?
> A. Define its width  B. Provide alternative text describing the image  C. Load the image faster  D. Center the image
> **Correct: B**

**Q5** — Skill: CSS | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> Which CSS layout system is specifically designed for two-dimensional row-and-column layouts?
> A. Flexbox  B. Grid  C. Float  D. Positioning
> **Correct: B**

**Q6** — Skill: CSS | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> Which CSS property controls the spacing between an element's content and its border?
> A. margin  B. padding  C. gap  D. outline
> **Correct: B**

**Q7** — Skill: CSS | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> You want three cards to appear in a flexible horizontal layout and wrap when space becomes limited. Which approach is appropriate?
> A. `display: flex` with wrapping enabled  B. `display: none`  C. `position: fixed`  D. `overflow: hidden`
> **Correct: A**

**Q8** — Skill: CSS | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> Which unit is commonly useful for creating dimensions that scale relative to the root font size?
> A. px  B. rem  C. pt  D. cm
> **Correct: B**

**Q9** — Skill: Responsive Design | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> A desktop layout breaks on narrow phone screens. What is an appropriate technique for adapting the layout at different viewport sizes?
> A. Media queries  B. SQL queries  C. Git branches  D. HTTP headers
> **Correct: A**

**Q10** — Skill: Accessibility | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> A form field has a visible text description. Which element should normally be associated with that field to provide a proper accessible label?
> A. `<label>`  B. `<span>`  C. `<br>`  D. `<hr>`
> **Correct: A**

**Q45** — Skill: Accessibility | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> A clickable interface element performs an action. Which is generally preferable for accessibility?
> A. A semantic `<button>`  B. A `<div>` with no semantics  C. A `<span>` with hidden text  D. An empty image
> **Correct: A**

**Q46** — Skill: Accessibility | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> A website must be usable with keyboard navigation. Which practice supports this?
> A. Ensure interactive controls can receive appropriate keyboard focus  B. Remove all focus indicators  C. Make all controls mouse-only  D. Replace buttons with images
> **Correct: A**

**Q47** — Skill: Accessibility | Type: scenario_judgment | Requires Tier-2 flag: HTML/CSS
> Why are semantic HTML elements valuable for accessibility?
> A. They communicate the meaning and role of content to browsers and assistive technologies  B. They automatically improve database performance  C. They eliminate JavaScript  D. They prevent all CSS bugs
> **Correct: A**

### JavaScript / TypeScript / Debugging (16 questions)

**Q11** — Skill: JavaScript | Type: code_output_prediction | Requires Tier-2 flag: JavaScript
> What does this code print?
> ```js
> const nums = [1, 2, 3];
> const result = nums.map(x => x * 2);
> console.log(result);
> ```
> A. `[1, 2, 3]`  B. `[2, 4, 6]`  C. `[1, 4, 9]`  D. `6`
> **Correct: B**

**Q12** — Skill: JavaScript | Type: code_output_prediction | Requires Tier-2 flag: JavaScript
> What does this code print?
> ```js
> console.log(typeof "hello");
> ```
> A. text  B. String  C. string  D. char
> **Correct: C**

**Q13** — Skill: JavaScript | Type: code_output_prediction | Requires Tier-2 flag: JavaScript
> What does `filter` do in this example?
> ```js
> const nums = [1, 2, 3, 4];
> const result = nums.filter(x => x > 2);
> ```
> A. Changes every value  B. Returns values satisfying the condition  C. Sorts the array  D. Converts the array to a string
> **Correct: B**

**Q14** — Skill: JavaScript | Type: code_output_prediction | Requires Tier-2 flag: JavaScript
> What is the value of `x`?
> ```js
> const x = { name: "Ana" };
> console.log(x.name);
> ```
> A. undefined  B. Ana  C. `{ name: "Ana" }`  D. name
> **Correct: B**

**Q15** — Skill: JavaScript | Type: scenario_judgment | Requires Tier-2 flag: JavaScript
> Which keyword is commonly used to declare a block-scoped variable that can be reassigned?
> A. const  B. let  C. static  D. define
> **Correct: B**

**Q16** — Skill: JavaScript | Type: scenario_judgment | Requires Tier-2 flag: JavaScript
> Which method converts a JSON string into a JavaScript object?
> A. `JSON.parse()`  B. `JSON.stringify()`  C. `JSON.convert()`  D. `JSON.object()`
> **Correct: A**

**Q17** — Skill: JavaScript | Type: code_output_prediction | Requires Tier-2 flag: JavaScript
> What does this print?
> ```js
> const a = [1, 2];
> a.push(3);
> console.log(a.length);
> ```
> A. 2  B. 3  C. 4  D. undefined
> **Correct: B**

**Q20** — Skill: JavaScript | Type: code_output_prediction | Requires Tier-2 flag: JavaScript
> What is the result?
> ```js
> const user = { name: "Sam" };
> console.log(user.age);
> ```
> A. 0  B. false  C. undefined  D. null
> **Correct: C**

**Q18** — Skill: TypeScript | Type: scenario_judgment | Requires Tier-2 flag: JavaScript
> What is one primary benefit of TypeScript over plain JavaScript?
> A. It adds static type checking  B. It removes the need for HTML  C. It replaces CSS  D. It prevents all runtime errors
> **Correct: A**

**Q56** — Skill: TypeScript | Type: scenario_judgment | Requires Tier-2 flag: JavaScript
> What does this TypeScript definition indicate?
> ```ts
> function add(a: number, b: number): number
> ```
> A. The function takes two numbers and returns a number  B. The function accepts any type and returns HTML  C. The function accepts strings only  D. The function cannot return anything
> **Correct: A**

**Q57** — Skill: TypeScript | Type: scenario_judgment | Requires Tier-2 flag: JavaScript
> Why can TypeScript catch some mistakes before the application runs?
> A. It performs static type checking during development/build processes  B. It replaces the browser  C. It guarantees every runtime condition is correct  D. It removes JavaScript execution
> **Correct: A**

**Q19** — Skill: Debugging | Type: scenario_judgment | Requires Tier-2 flag: JavaScript
> A click handler runs twice when you expected it once. What is a reasonable first debugging step?
> A. Inspect how many event listeners are being attached  B. Delete the entire component  C. Remove the browser  D. Change the database schema
> **Correct: A**

**Q54** — Skill: Debugging | Type: scenario_judgment | Requires Tier-2 flag: JavaScript
> A button's click handler appears not to run. What should you inspect first?
> A. Whether the handler is actually attached and invoked  B. The database primary key  C. The server operating system  D. The image compression format
> **Correct: A**

**Q49** — Skill: Performance | Type: scenario_judgment | Requires Tier-2 flag: JavaScript
> A page loads a very large JavaScript bundle even though some features are rarely used. Which technique can help reduce initial loading work?
> A. Code splitting or lazy loading  B. Copy the bundle multiple times  C. Disable compression  D. Add more global variables
> **Correct: A**

**Q52** — Skill: Testing | Type: scenario_judgment | Requires Tier-2 flag: JavaScript
> What is the main purpose of a frontend unit test?
> A. Verify a small piece of frontend logic or behavior in isolation  B. Deploy the application  C. Configure DNS  D. Replace the browser
> **Correct: A**

**Q41** — Skill: Forms & Validation | Type: scenario_judgment | Requires Tier-2 flag: JavaScript
> A login form requires an email address. What should happen before sending the form to the backend?
> A. Validate that the required field has an acceptable value  B. Automatically assume the value is valid  C. Skip all validation  D. Store the email as CSS
> **Correct: A**

**Q44** — Skill: Forms & Validation | Type: scenario_judgment | Requires Tier-2 flag: JavaScript
> Why should client-side validation not be treated as the only validation layer for sensitive operations?
> A. The backend can receive requests that bypass the browser UI  B. CSS performs validation automatically  C. HTML cannot contain forms  D. Browsers never execute JavaScript
> **Correct: A**

### React (13 questions)

**Q21** — Skill: React | Type: code_output_prediction | Requires Tier-2 flag: React
> What is the main purpose of React state?
> A. Store values that can affect rendering and change over time  B. Replace HTML  C. Store database credentials  D. Define CSS media queries
> **Correct: A**

**Q22** — Skill: React | Type: scenario_judgment | Requires Tier-2 flag: React
> A child component needs data supplied by its parent. What is the normal React mechanism?
> A. Props  B. SQL  C. Cookies only  D. CSS variables
> **Correct: A**

**Q23** — Skill: React | Type: scenario_judgment | Requires Tier-2 flag: React
> Which hook is commonly used to store local component state?
> A. useState  B. useRoute  C. useStyle  D. useHTML
> **Correct: A**

**Q24** — Skill: React | Type: scenario_judgment | Requires Tier-2 flag: React
> A component needs to perform a side effect after rendering, such as fetching data. Which hook is commonly used?
> A. useEffect  B. useArray  C. useClass  D. useStatic
> **Correct: A**

**Q25** — Skill: React | Type: scenario_judgment | Requires Tier-2 flag: React
> Why should React lists generally provide a stable key for each item?
> A. To help React identify list items across renders  B. To encrypt the item  C. To make CSS load faster  D. To create database indexes
> **Correct: A**

**Q26** — Skill: React | Type: code_output_prediction | Requires Tier-2 flag: React
> Given:
> ```jsx
> function User({ name }) {
>   return <h2>{name}</h2>;
> }
> ```
> What value is received through `name` when rendering `<User name="Riya" />`?
> A. User  B. Riya  C. name  D. undefined
> **Correct: B**

**Q27** — Skill: React | Type: scenario_judgment | Requires Tier-2 flag: React
> A form input should reflect a value stored in React state. What is this commonly called?
> A. Controlled input  B. Detached input  C. Static input  D. Database input
> **Correct: A**

**Q28** — Skill: React | Type: scenario_judgment | Requires Tier-2 flag: React
> A component contains the same UI structure in several places. What is a good React practice?
> A. Create a reusable component  B. Copy the same markup everywhere  C. Store the markup in a database  D. Replace React with SQL
> **Correct: A**

**Q29** — Skill: React | Type: scenario_judgment | Requires Tier-2 flag: React
> A state update depends on the previous state value. Which approach is safest?
> A. Use the functional form of the state updater  B. Mutate the state object directly  C. Reload the page  D. Store the value in HTML
> **Correct: A**

**Q30** — Skill: React | Type: scenario_judgment | Requires Tier-2 flag: React
> A component's UI should change when a user selects a filter. What should normally drive that change?
> A. State or props  B. Database schema  C. Git tags  D. CSS comments
> **Correct: A**

**Q42** — Skill: Forms & Validation | Type: scenario_judgment | Requires Tier-2 flag: React
> A form submission causes the browser to refresh the page even though the application should handle it in JavaScript. Which event behavior is commonly needed?
> A. Prevent the default form submission behavior  B. Disable all JavaScript  C. Remove the form element  D. Clear the browser cache
> **Correct: A**

**Q43** — Skill: Forms & Validation | Type: scenario_judgment | Requires Tier-2 flag: React
> A required form field is empty. What is a useful user-facing response?
> A. Show a validation message explaining that the field is required  B. Submit the form anyway  C. Hide the entire application  D. Delete the entered values
> **Correct: A**

**Q53** — Skill: Testing | Type: scenario_judgment | Requires Tier-2 flag: React
> A React component displays the wrong text under a particular state. What is a useful test?
> A. Render the component in that state and verify the expected output  B. Test only the database schema  C. Test the Git history  D. Change the CSS before testing
> **Correct: A**

**Q55** — Skill: Debugging | Type: scenario_judgment | Requires Tier-2 flag: React
> A component keeps re-rendering unexpectedly after a state change. What is a useful debugging step?
> A. Inspect the state updates and effect dependencies causing the renders  B. Delete the component immediately  C. Remove all HTML  D. Change the database engine
> **Correct: A**

**Q48** — Skill: Performance | Type: scenario_judgment | Requires Tier-2 flag: React
> A React application renders a very large list and becomes slow. Which technique can reduce unnecessary DOM work?
> A. Virtualize the visible portion of the list  B. Add more duplicate elements  C. Disable all event handling  D. Put the list in CSS comments
> **Correct: A**

**Q50** — Skill: Performance | Type: scenario_judgment | Requires Tier-2 flag: React
> A child component performs expensive rendering even though its relevant props have not changed. What React technique may help in suitable cases?
> A. Memoization  B. Adding more state  C. Reloading the browser every second  D. Removing all props
> **Correct: A**

**Q58** — Skill: UI Component Design | Type: scenario_judgment | Requires Tier-2 flag: React
> A design system contains buttons that are reused throughout an application. What is the strongest reason to create a reusable Button component?
> A. Centralize shared behavior and presentation  B. Prevent all JavaScript execution  C. Replace the API layer  D. Store user passwords
> **Correct: A**

### API Integration (7 questions)

**Q31** — Skill: API Integration | Type: scenario_judgment | Requires Tier-2 flag: API Integration
> A frontend needs data from `/api/products`. What is a common browser-side mechanism for requesting it?
> A. `fetch()`  B. `git pull`  C. `console.database()`  D. `renderAPI()`
> **Correct: A**

**Q32** — Skill: API Integration | Type: scenario_judgment | Requires Tier-2 flag: API Integration
> A fetch request succeeds at the network level but the server returns HTTP 404. What should the frontend recognize?
> A. The requested resource was not found  B. The request definitely succeeded with valid data  C. The browser is offline  D. The JavaScript file failed to parse
> **Correct: A**

**Q33** — Skill: API Integration | Type: scenario_judgment | Requires Tier-2 flag: API Integration
> While API data is loading, what is a useful UI behavior?
> A. Show a loading state  B. Pretend the final data is already available  C. Delete the component  D. Disable JavaScript permanently
> **Correct: A**

**Q34** — Skill: API Integration | Type: scenario_judgment | Requires Tier-2 flag: API Integration
> An API request fails because of a network problem. What should a well-designed frontend generally do?
> A. Provide an appropriate error state or retry option  B. Display fake successful data as fact  C. Ignore the failure silently in every case  D. Delete the user's account
> **Correct: A**

**Q35** — Skill: API Integration | Type: scenario_judgment | Requires Tier-2 flag: API Integration
> The API returns JSON representing a list of products. What should the frontend generally do before rendering the data?
> A. Parse and use the returned data according to the expected structure  B. Treat the entire response as CSS  C. Send it directly to Git  D. Convert it into SQL
> **Correct: A**

**Q36** — Skill: API Integration | Type: scenario_judgment | Requires Tier-2 flag: API Integration
> A frontend page requires authentication to access an API. Where should sensitive authentication information generally be handled according to the application's security design?
> A. Through an appropriately secured authentication mechanism  B. In visible page text  C. Inside public CSS  D. In the image filename
> **Correct: A**

**Q51** — Skill: Performance | Type: scenario_judgment | Requires Tier-2 flag: API Integration
> A page performs the same API request repeatedly even though the returned data changes rarely. What is a reasonable optimization?
> A. Cache the response where appropriate  B. Increase the request frequency  C. Make duplicate requests simultaneously  D. Disable HTTP
> **Correct: A**

### State Management (4 questions)

**Q37** — Skill: State Management | Type: scenario_judgment | Requires Tier-2 flag: State Management
> A shopping cart must be available to many unrelated components. What is a reasonable reason to use shared state?
> A. Multiple components need access to the same changing data  B. CSS cannot use classes  C. HTML cannot contain buttons  D. Git requires it
> **Correct: A**

**Q38** — Skill: State Management | Type: scenario_judgment | Requires Tier-2 flag: State Management
> A state object is treated as immutable. When updating one property, what is generally preferred?
> A. Create an updated object rather than directly mutating the existing state  B. Modify the original object silently  C. Delete the state variable  D. Reload the server
> **Correct: A**

**Q39** — Skill: State Management | Type: scenario_judgment | Requires Tier-2 flag: State Management
> A user changes a filter, and several components need to react to that change. What is the main reason to keep that filter value in shared state?
> A. It provides a common source of truth  B. It automatically writes SQL  C. It replaces JavaScript  D. It disables re-rendering
> **Correct: A**

**Q40** — Skill: State Management | Type: scenario_judgment | Requires Tier-2 flag: State Management
> What is generally undesirable when managing application state?
> A. Having multiple conflicting sources of truth for the same data  B. Giving related components access to needed state  C. Updating state through the appropriate mechanism  D. Keeping state scoped when possible
> **Correct: A**

### Project-Informed Adaptive Questions (2, selected via Tier 2b context)

**Q59** — Skill: Project-Informed React | Type: scenario_judgment | Requires Tier-2 flag: React
> *Example trigger: student describes building an e-commerce React app with a product list, cart, and checkout flow.*
> The cart count is displayed in the header and also inside the cart page. What is the strongest reason to keep the cart data in shared state accessible to both areas?
> A. Both parts need access to the same changing cart information  B. The header cannot contain HTML  C. React cannot render arrays  D. CSS requires global state
> **Correct: A**

**Q60** — Skill: Project-Informed API Integration | Type: scenario_judgment | Requires Tier-2 flag: API Integration
> *Example trigger: student describes a project that consumed a product API and displayed results in a React interface.*
> The API request is still pending when the component first renders. What should the interface normally account for?
> A. A loading state before the data arrives  B. Treating the response as already available  C. Assuming the request always succeeds  D. Removing the component until the server responds
> **Correct: A**

*(Note: only two project-informed templates exist so far — more variants for other common project types can be added later; not required to unblock the build.)*

---

## POOL SUMMARY

| Area | Candidate Questions |
|---|---|
| HTML / CSS / Responsive / Accessibility | 13 |
| JavaScript / TypeScript / Debugging | 16 |
| React | 13 |
| API Integration | 7 |
| State Management | 4 |
| Project-informed | 2 |
| Forms & Validation (clustered above) | 5 |
| **Total** | **60** (all grading is exact-match MCQ, deterministic, no model involved) |

**Reminder for Astra:** serve a maximum of 15 of these per student, same adaptive selection logic as Backend. This is content only — no changes to matching algorithm, DB schema, data pipeline, or any other module. The Frontend pool intentionally tests different competencies than Backend (DOM/CSS semantics, JS behavior, React architecture, accessibility, frontend performance) rather than reusing Backend's question shapes with renamed skills.

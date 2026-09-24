// DocIndeX — dropzone interaction
(function () {
  const input   = document.getElementById("pdf");
  const inner   = document.getElementById("dropzone-inner");
  const lead    = document.getElementById("dz-lead");
  const hint    = document.getElementById("dz-hint");
  const submit  = document.getElementById("submit");

  function isPdf(file) {
    return file && file.name.toLowerCase().endsWith(".pdf");
  }

  function setFile(file) {
    if (!isPdf(file)) {
      inner.classList.remove("has-file");
      lead.textContent = "PDF files only";
      hint.innerHTML = 'or <button type="button" class="linklike" id="browse">choose a file</button> · .pdf only';
      rebind();
      submit.disabled = true;
      return;
    }
    inner.classList.add("has-file");
    lead.textContent = file.name;
    const kb = Math.max(1, Math.round(file.size / 1024));
    hint.textContent = kb + " KB · ready to index";
    submit.disabled = false;
  }

  function rebind() {
    const b = document.getElementById("browse");
    if (b) b.addEventListener("click", () => input.click());
  }

  inner.addEventListener("click", (e) => {
    if (e.target.id !== "browse") input.click();
  });
  rebind();

  input.addEventListener("change", () => {
    if (input.files.length) setFile(input.files[0]);
  });

  // drag & drop
  ["dragenter", "dragover"].forEach((ev) =>
    inner.addEventListener(ev, (e) => {
      e.preventDefault();
      inner.classList.add("is-drag");
    })
  );
  ["dragleave", "drop"].forEach((ev) =>
    inner.addEventListener(ev, (e) => {
      e.preventDefault();
      inner.classList.remove("is-drag");
    })
  );
  inner.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) {
      input.files = e.dataTransfer.files;
      setFile(file);
    }
  });
})();

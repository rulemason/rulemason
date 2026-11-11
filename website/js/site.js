// 落地页小交互：复制安装命令、终端逐行打出真实输出并循环、滚进视口时淡入。减少动效时都不动。

(function () {
  // 1. 复制按钮默认藏着，脚本跑起来再显示
  var buttons = document.querySelectorAll(".copy");
  for (var i = 0; i < buttons.length; i++) {
    bindCopy(buttons[i]);
  }
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) {
    return;
  }
  // 2. 终端：先打命令，再逐行放出真实输出，打完循环
  var terms = document.querySelectorAll("[data-term]");
  for (var t = 0; t < terms.length; t++) {
    playTerm(terms[t]);
  }
  // 3. 下方区块滚进来再出现
  revealOnScroll();
})();

function bindCopy(button) {
  button.hidden = false;
  button.addEventListener("click", function () {
    var pre = document.getElementById(button.getAttribute("data-for"));
    var status = document.getElementById("copy-status");
    var cmd = pre.textContent.replace(/^\n+|\n+$/g, "");
    // 走到这里说明按钮、命令和状态区都在页面上
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(cmd).then(function () {
        markCopied(button, status);
      }, function () {
        copyFromSelection(pre, button, status);
      });
      return;
    }
    copyFromSelection(pre, button, status);
  });
}

function markCopied(button, status) {
  var done = button.getAttribute("data-done");
  status.textContent = done;
  var previous = button.textContent;
  button.textContent = done;
  window.setTimeout(function () {
    button.textContent = previous;
    if (status.textContent === done) {
      status.textContent = "";
    }
  }, 2000);
}

function copyFromSelection(pre, button, status) {
  var range = document.createRange();
  range.selectNodeContents(pre);
  var selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  var ok = false;
  try {
    ok = document.execCommand("copy");
  } catch (err) {
    ok = false;
  }
  if (ok) {
    markCopied(button, status);
    return;
  }
  status.textContent = button.getAttribute("data-fail");
}

function playTerm(term) {
  var lines = term.querySelectorAll(".term-line");
  var screen = term.querySelector(".term-screen");
  var cmd = term.querySelector(".cmd-text");
  var full = cmd.textContent;
  var timer = 0;
  var pending = null;
  var due = 0;
  var paused = document.hidden;

  function arm(fn, ms) {
    pending = fn;
    due = Date.now() + ms;
    window.clearTimeout(timer);
    timer = 0;
    if (paused) {
      // 走到这里说明标签页在后台，这一步先记着，等回来再打
      return;
    }
    timer = window.setTimeout(function () {
      timer = 0;
      fn();
    }, ms);
  }

  document.addEventListener("visibilitychange", function () {
    paused = document.hidden;
    if (paused) {
      window.clearTimeout(timer);
      timer = 0;
      return;
    }
    if (pending && !timer) {
      arm(pending, Math.max(0, due - Date.now()));
    }
  });

  function begin() {
    // 1. 清空后逐字打命令
    term.classList.add("is-playing");
    for (var k = 0; k < lines.length; k += 1) {
      lines[k].classList.remove("is-on");
    }
    lines[0].classList.add("is-on");
    cmd.textContent = "";
    screen.scrollTop = 0;
    var i = 0;
    function typeCmd() {
      i += 1;
      cmd.textContent = full.slice(0, i);
      if (i < full.length) {
        arm(typeCmd, 28);
        return;
      }
      // 2. 命令打完，按行放出真实输出，并滚到新行
      var n = 1;
      function showNext() {
        if (n >= lines.length) {
          // 3. 停几秒让人读完最后几行，再从头打
          arm(begin, 4000);
          return;
        }
        lines[n].classList.add("is-on");
        screen.scrollTop = screen.scrollHeight;
        n += 1;
        arm(showNext, 220);
      }
      arm(showNext, 280);
    }
    arm(typeCmd, 400);
  }

  begin();
}

function revealOnScroll() {
  var blocks = document.querySelectorAll(".reveal");
  if (!blocks.length || !("IntersectionObserver" in window)) {
    return;
  }
  for (var i = 0; i < blocks.length; i++) {
    blocks[i].classList.add("will-reveal");
  }
  var observer = new IntersectionObserver(function (entries) {
    for (var n = 0; n < entries.length; n++) {
      if (entries[n].isIntersecting) {
        entries[n].target.classList.add("is-in");
        observer.unobserve(entries[n].target);
      }
    }
  }, { rootMargin: "0px 0px -8% 0px" });
  for (var j = 0; j < blocks.length; j++) {
    observer.observe(blocks[j]);
  }
}

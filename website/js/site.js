// 落地页上的两件小事：复制安装命令，以及在减少动效时把演示 GIF 换成静帧。

(function () {
  // 1. 复制按钮默认藏着，脚本跑起来再显示，没开脚本时只留下可选中的命令
  var buttons = document.querySelectorAll(".copy");
  for (var i = 0; i < buttons.length; i++) {
    bindCopy(buttons[i]);
  }

  // 2. 用户要求减少动效时，循环 GIF 换成各自的第一帧
  var motion = window.matchMedia("(prefers-reduced-motion: reduce)");
  applyMotion(motion.matches);
  if (motion.addEventListener) {
    motion.addEventListener("change", function (event) {
      applyMotion(event.matches);
    });
  }
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

function applyMotion(reduce) {
  var shots = document.querySelectorAll("img[data-still]");
  for (var i = 0; i < shots.length; i++) {
    var img = shots[i];
    if (!img.getAttribute("data-live")) {
      img.setAttribute("data-live", img.getAttribute("src"));
    }
    img.setAttribute("src", reduce ? img.getAttribute("data-still") : img.getAttribute("data-live"));
  }
}

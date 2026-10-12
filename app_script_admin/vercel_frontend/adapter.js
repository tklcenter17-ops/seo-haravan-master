// ============================================================
// Google Apps Script Adapter Bridge for Vercel & VPS (Version 2.0)
// 100% Compliant with Google Apps Script Client API Builder Pattern
// ============================================================

(function () {
  function createGasRunner(options) {
    const state = {
      successHandler: (options && options.successHandler) || null,
      failureHandler: (options && options.failureHandler) || null,
      userObject: (options && options.userObject) || null
    };

    const baseTarget = {
      withSuccessHandler: function (fn) {
        return createGasRunner({
          successHandler: fn,
          failureHandler: state.failureHandler,
          userObject: state.userObject
        });
      },
      withFailureHandler: function (fn) {
        return createGasRunner({
          successHandler: state.successHandler,
          failureHandler: fn,
          userObject: state.userObject
        });
      },
      withUserObject: function (obj) {
        return createGasRunner({
          successHandler: state.successHandler,
          failureHandler: state.failureHandler,
          userObject: obj
        });
      }
    };

    return new Proxy(baseTarget, {
      get: function (target, prop) {
        if (prop in target) {
          return target[prop];
        }

        // Any server-side function call: .login(...), .getCrmSyncSnapshot(...), .getAllRows(...)
        return function (...args) {
          const fnName = String(prop);
          fetch(`/api/gas/${fnName}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ args: args })
          })
            .then(async function (res) {
              if (!res.ok) {
                const txt = await res.text();
                throw new Error(`HTTP ${res.status}: ${txt}`);
              }
              return res.json();
            })
            .then(function (data) {
              if (data && data.success) {
                if (state.successHandler) {
                  try {
                    state.successHandler(data.result, state.userObject);
                  } catch (uiErr) {
                    console.error(`[UI Render Error in ${fnName}]:`, uiErr);
                  }
                }
              } else {
                const err = new Error((data && data.error) || `Lỗi khi gọi hàm ${fnName}`);
                if (state.failureHandler) {
                  state.failureHandler(err, state.userObject);
                } else {
                  console.error(`[GAS Bridge] Error in ${fnName}:`, err);
                }
              }
            })
            .catch(function (err) {
              console.error(`[GAS Bridge] Network error in ${fnName}:`, err);
              if (state.failureHandler) {
                state.failureHandler(err, state.userObject);
              }
            });
        };
      }
    });
  }

  window.google = window.google || {};
  window.google.script = window.google.script || {};
  window.google.script.run = createGasRunner({});
})();

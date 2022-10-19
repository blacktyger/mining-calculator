
document.addEventListener('DOMContentLoaded', function () {
  function keep_alive_server() {
    fetch(document.location + "random-endpoint", {
      method: 'GET',
      cache: 'no-cache'
    })
      .then(res => { })
      .catch(err => { })
  }

  try {
    setInterval(keep_alive_server, 3 * 1000)()
  } catch (error) {
    // doesn't matter handled by middleware
  }
})

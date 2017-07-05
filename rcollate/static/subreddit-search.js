SEARCH_REQUEST_INTERVAL = 500;

lastSearchRequestTime = 0;
lastSearchRequestSubreddit = "";

$subredditInput = null;

function sendSubredditSearchRequest(socket, subreddit) {
  now = (new Date()).getTime();

  if (now - lastSearchRequestTime < SEARCH_REQUEST_INTERVAL)
    return;

  if (subreddit == lastSearchRequestSubreddit)
    return;

  lastSearchRequestTime = now;
  lastSearchRequestSubreddit = subreddit;

  socket.emit('subreddit_search_request', {
    subreddit: subreddit
  });
}

function receiveSubredditSearchResponse(msg) {
  if (msg.subreddit != $subredditInput.val())
    return;

  if (!$subredditInput.is(":focus"))
    return;

  // update suggestions
  $subredditInput.autocomplete("option", {
    source: msg.matches
  });

  // show new suggestions
  $subredditInput.autocomplete("search");
}

$(document).ready(function() {
  var socket = io.connect();

  socket.on('subreddit_search_response', receiveSubredditSearchResponse);

  $subredditInput = $('input[name="subreddit"]');
  $subredditInput.autocomplete({
    source: [],
    autoFocus: true, // allow enter to select first option
    focus: function(event, ui) {
      // prevent suggestions being refreshed while toggling through suggestions
      lastSearchRequestSubreddit = ui.item.value;
    },
    select: function(event, ui) {
      // prevent suggestions for selected value
      lastSearchRequestSubreddit = ui.item.value;
      $subredditInput.autocomplete("option", { source: [] });
    }
  });
  $subredditInput.on({
    keypress: function(event) {
      var code = (event.keyCode ? event.keyCode : event.which);
      if (code == 37 || code == 39) {
        // hide and prevent suggestions after selecting with left/right keys
        lastSearchRequestSubreddit = $subredditInput.val();
        $subredditInput.autocomplete("option", { source: [] });
        $subredditInput.autocomplete("close");
      }
    }
  });

  lastSearchRequestSubreddit = $subredditInput.val();

  setInterval(function() {
    sendSubredditSearchRequest(socket, $subredditInput.val());
  }, SEARCH_REQUEST_INTERVAL);

  $('input[name="subreddit"]').on('input', function(e) {
    sendSubredditSearchRequest(socket, $subredditInput.val());
  });
});

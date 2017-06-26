SEARCH_REQUEST_INTERVAL = 500;

lastSearchRequestTime = 0;
lastSearchRequestSubreddit = "";

function sendSubredditSearchRequest(socket, subreddit) {
  now = (new Date()).getTime();

  if (now - lastSearchRequestTime < SEARCH_REQUEST_INTERVAL)
    return;

  if (subreddit == lastSearchRequestSubreddit)
    return;

  lastSearchRequestTime = now;
  lastSearchRequestSubreddit = subreddit;

  socket.emit('subreddit_search_request', {
    request_time: now,
    subreddit: subreddit
  });
}

function receiveSubredditSearchResponse(msg) {
  if (msg.request_time != lastSearchRequestTime)
    return;

  $('#subreddit_matches').html(msg.matches.join("<br/>"));
}

$(document).ready(function() {
  var socket = io.connect();

  socket.on('subreddit_search_response', receiveSubredditSearchResponse);

  $subredditInput = $('input[name="subreddit"]');
  lastSearchRequestSubreddit = $subredditInput.val();

  setInterval(function() {
    sendSubredditSearchRequest(socket, $subredditInput.val());
  }, SEARCH_REQUEST_INTERVAL);

  $('input[name="subreddit"]').on('input', function(e) {
    sendSubredditSearchRequest(socket, $subredditInput.val());
  });
});

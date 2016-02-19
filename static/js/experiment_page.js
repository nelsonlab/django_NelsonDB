function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie != '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = jQuery.trim(cookies[i]);
			// Does this cookie string begin with the name we want?
			if (cookie.substring(0, name.length + 1) == (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}

function csrfSafeMethod(method) {
	// these HTTP methods do not require CSRF protection
	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
	// test that a given url is a same-origin URL
	// url could be relative or scheme relative or absolute
	var host = document.location.host; // host + port
	var protocol = document.location.protocol;
	var sr_origin = '//' + host;
	var origin = protocol + sr_origin;
	// Allow absolute or scheme relative URLs to same origin
	return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
	(url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
	// or any other URL that isn't scheme relative or absolute i.e relative.
	!(/^(\/\/|http:|https:).*/.test(url));
}

$('#experiment_page_delete_experiment_button').click(function(){
	if (confirm("Are you sure you want to delete this experiment and all associated data? It cannot be undone.")) {
		$.ajax({
			dataType: "json",
			url: "/lab/experiment_delete/",
			type: "POST",
			data: {'experiment_id':$('#experiment_page_experiment_id').val()},
			beforeSend: function(xhr, settings) {
				var csrftoken = getCookie('csrftoken');
				if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
					xhr.setRequestHeader("X-CSRFToken", csrftoken);
				}
			},
			success: function(data) {
				alert(data.message);
				location.reload();
			}
		});
	}
});
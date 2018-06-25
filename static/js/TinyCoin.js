var method = "GET";
function onBlocksClick(){
	$("#url").html("/blocks");
	$("#textInput").html('');
	$("#textOutput").html('');
	method = "GET";
}

function onPingClick(){
	$("#url").html("/ping");
	$("#textInput").html('');
	$("#textOutput").html('');
	method = "GET";
}

function onMineClick(){
	$("#url").html("/mine");
	$("#textInput").html('');
	$("#textOutput").html('');
	method = "GET";
}

function onConsensusClick(){
	$("#url").html("/consensus");
	$("#textInput").html('');
	$("#textOutput").html('');
	method = "GET";
}

function onTransactionClick(){
	$("#url").html("/txion");
	$("#textInput").html('{"from":"from_people", "to":"to_people", "amount":1}');
	$("#textOutput").html('');
	method = "POST";
}

function onSubmitClick(){
	var url = $("#url").html();
	var data = $("#textInput").html();

	$.ajax({
		  type: method,
		  url: url,
		  data: data,
		  contentType: 'application/json;charset=UTF-8',
		  success: function(data) {
			  $("#textOutput").html(data)
		  },
		});
}
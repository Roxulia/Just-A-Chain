<?php
$servername = "";
$username = "";
$password = "";
$dbname = "";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Handle API requests
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_GET['action'])) {
    $action = $_GET['action'];

    switch ($action) {
        case 'register_node':
            registerNode($conn);
            break;
        default:
            response(400, "Invalid action");
            break;
    }
} elseif ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['action'])) {
    $action = $_GET['action'];

    switch ($action) {
        case 'get_all_nodes':
            getAllNodes($conn);
            break;
        case 'check_node':
            checkNodes($conn);
            break;
        default:
            response(400, "Invalid action");
            break;
    }
} else {
    response(400, "Invalid request method");
}

// Function to register a node
function registerNode($conn) {
    $node_id = $_POST['node_id'];
    $ip_address = $_POST['node'];

    if (empty($node_id) || empty($ip_address)) {
        response(400, "Node ID and links are required");
        return;
    }

    $stmt = $conn->prepare("INSERT INTO nodes (node_id, link) VALUES (?, ?)");
    $stmt->bind_param("ss", $node_id, $ip_address);

    if ($stmt->execute()) {
        response(200, "Node registered successfully");
    } else {
        response(500, "Failed to register node");
    }

    $stmt->close();
}

// Function to get all nodes
function getAllNodes($conn) {
    $sql = "SELECT  link FROM nodes";
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        $nodes = [];
        while($row = $result->fetch_assoc()) {
            $nodes[] = $row;
        }
        response(200, $nodes);
    } else {
        response(400, []);
    }
}

function checkNodes($db) {
    $stmt = $db->query("SELECT id, node_id,link FROM nodes");
    $nodes = $stmt->fetchAll(PDO::FETCH_ASSOC);

    foreach ($nodes as $node) {
        $url = "{$nodes['link']}/check";

        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5); // Set timeout to 5 seconds

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode != 200 || !$response) {
            // Remove node if it does not respond correctly
            $stmtDelete = $db->prepare("DELETE FROM nodes WHERE id = :id");
            $stmtDelete->bindParam(':id', $node['id']);
            $stmtDelete->execute();
        }
    }}
// Function to handle API responses
function response($status, $data) {
    header("Content-Type: application/json");
    http_response_code($status);
    echo json_encode($data);
}

$conn->close();
?>

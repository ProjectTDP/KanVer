# KanVer API Test Script
Write-Host "Testing KanVer API..." -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "Test 1: Health Endpoint" -ForegroundColor Yellow
$health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | ConvertFrom-Json
Write-Host "Status: $($health.status)" -ForegroundColor Green
Write-Host ""

# Test 2: Root Endpoint
Write-Host "Test 2: Root Endpoint" -ForegroundColor Yellow
$root = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing | ConvertFrom-Json
Write-Host "Message: $($root.message)" -ForegroundColor Green
Write-Host ""

# Test 3: Register User
Write-Host "Test 3: User Registration" -ForegroundColor Yellow
$registerData = @{
    phone_number = "05551234567"
    password = "TestPass123!"
    full_name = "Test User"
    email = "test@example.com"
    date_of_birth = "1995-05-15"
    blood_type = "A+"
} | ConvertTo-Json

try {
    $register = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/register" `
        -Method POST `
        -ContentType "application/json" `
        -Body $registerData `
        -UseBasicParsing | ConvertFrom-Json
    
    Write-Host "Registration successful!" -ForegroundColor Green
    Write-Host "User ID: $($register.user.user_id)" -ForegroundColor Green
    Write-Host "Phone: $($register.user.phone_number)" -ForegroundColor Green
    
    $accessToken = $register.tokens.access_token
    $refreshToken = $register.tokens.refresh_token
    Write-Host ""
    
    # Test 4: Login
    Write-Host "Test 4: User Login" -ForegroundColor Yellow
    $loginData = @{
        phone_number = "05551234567"
        password = "TestPass123!"
    } | ConvertTo-Json
    
    $login = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginData `
        -UseBasicParsing | ConvertFrom-Json
    
    Write-Host "Login successful!" -ForegroundColor Green
    Write-Host ""
    
    # Test 5: Refresh Token
    Write-Host "Test 5: Token Refresh" -ForegroundColor Yellow
    $refreshData = @{
        refresh_token = $refreshToken
    } | ConvertTo-Json
    
    $refresh = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/refresh" `
        -Method POST `
        -ContentType "application/json" `
        -Body $refreshData `
        -UseBasicParsing | ConvertFrom-Json
    
    Write-Host "Token refresh successful!" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "All tests passed!" -ForegroundColor Green
    
} catch {
    Write-Host "Error occurred:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "Swagger UI: http://localhost:8000/docs" -ForegroundColor Cyan

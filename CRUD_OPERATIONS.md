# CRUD Operations - Courier Delivery System

## ✅ Complete CRUD Implementation

### CREATE (Create Package)
- **Endpoint**: `POST /api/packages`
- **Description**: Creates a new package with automatic distance and price calculation
- **Required Fields**:
  - `pickup_address` (with EIRCODE for Ireland)
  - `recipient_address` (with EIRCODE)
  - `recipient_name`
  - `recipient_email`
  - `weight_kg`
- **Response**: Returns package_id, tracking_id, distance, price, status
- **Email**: Sends email notification on creation (if email verified in SES)

### READ (Get Packages)
1. **List All Packages**
   - **Endpoint**: `GET /api/packages`
   - **Description**: Returns list of all packages (latest 10)
   - **Response**: Array of package objects

2. **Get Package by ID**
   - **Endpoint**: `GET /api/packages/id/<package_id>`
   - **Description**: Returns single package by ID
   - **Response**: Package object with all details

3. **Track Package by Tracking ID**
   - **Endpoint**: `GET /api/packages/<tracking_id>`
   - **Description**: Track package using tracking ID
   - **Response**: Package object

4. **Get Packages by Status**
   - **Endpoint**: `GET /api/packages/status/<status>`
   - **Description**: Filter packages by status (pending, assigned, in_transit, delivered, etc.)
   - **Response**: Array of packages with specified status

### UPDATE (Update Package)
1. **Update Package Details**
   - **Endpoint**: `PUT /api/packages/<package_id>`
   - **Description**: Update package information (addresses, name, email, weight)
   - **Fields**: recipient_name, recipient_email, recipient_address, pickup_address, weight_kg
   - **Response**: Updated package with recalculated distance and price

2. **Update Package Status**
   - **Endpoint**: `PUT /api/packages/<package_id>/status`
   - **Description**: Update package status
   - **Body**: `{"status": "pending|assigned|in_transit|delivered|cancelled"}`
   - **Response**: Success confirmation
   - **Email**: Sends status update email

### DELETE (Delete Package)
- **Endpoint**: `DELETE /api/packages/<package_id>`
- **Description**: Deletes a package from the system
- **Response**: Success confirmation with tracking_id
- **Email**: Sends deletion notification email

## 🌐 UI Features

### Create Package Tab
- Form with all required fields
- Email field for notifications
- Automatic distance and price calculation
- Success/error alerts

### All Packages Tab
- View all packages in cards
- **Edit Button**: Populates form for editing
- **Delete Button**: Deletes package (with confirmation)
- **Update Status Button**: Changes package status
- Real-time updates

### Track Package Tab
- Enter tracking ID
- View full package details
- Status information

## 📧 Email Notifications

### Email Events
1. **Package Created**: Sent when package is created
2. **Status Updated**: Sent when status changes
3. **Driver Assigned**: Sent when driver accepts delivery
4. **Package Deleted**: Sent when package is deleted

### Email Format
- HTML formatted emails
- Professional templates
- Includes tracking ID, status, addresses, price

### Email Verification
- AWS SES requires email verification
- Check inbox: abhisheksharma.irl@gmail.com
- Click verification link from AWS SES
- Once verified, emails send automatically

## 🧪 Testing

### Test via API
```bash
# CREATE
curl -X POST http://localhost:5000/api/packages \
  -H "Content-Type: application/json" \
  -d '{"pickup_address":"Dublin 2, D02 AF30","recipient_address":"Dublin 4, D04 XY12","recipient_name":"Test","recipient_email":"test@example.com","weight_kg":2.0}'

# READ
curl http://localhost:5000/api/packages
curl http://localhost:5000/api/packages/id/<package_id>

# UPDATE
curl -X PUT http://localhost:5000/api/packages/<package_id> \
  -H "Content-Type: application/json" \
  -d '{"recipient_name":"Updated Name","recipient_email":"test@example.com","recipient_address":"Dublin 6, D06 XY78","pickup_address":"Dublin 1, D01 AB12","weight_kg":3.0}'

# DELETE
curl -X DELETE http://localhost:5000/api/packages/<package_id>
```

### Test via UI
1. Open: http://localhost:5000/
2. Create a package with your email
3. View packages and test Edit/Delete buttons
4. Update status and verify email (once verified)

## ✅ Status

All CRUD operations are fully implemented and tested:
- ✅ CREATE: Working
- ✅ READ: Working (multiple endpoints)
- ✅ UPDATE: Working (details and status)
- ✅ DELETE: Working
- ✅ UI: All features working
- ✅ Email: Code working (verification required)
- ✅ SNS: Working


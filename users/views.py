from rest_framework.views import APIView, Response
from .models import User
from .serializers import UserSerializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken



class UserRegisterView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        if request.user.is_anonymous:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)
        
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        print("Reached here")
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully", "user": serializer.data}, status=201)
        return Response(serializer.errors, status=400)


class UserLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                serializer = UserSerializer(user)
                refresh_token = RefreshToken.for_user(user)
                serializer_data = serializer.data
                serializer_data['access'] = str(refresh_token.access_token)
                serializer_data['message'] = "Login successful"
                response = Response({serializer_data})
                response.set_cookie(
                    key='refresh_token',
                    value=str(refresh_token),
                    httponly=True,
                    secure=True,
                    samesite='Lax'
                )
                
                return response
            else:
                return Response({"detail": "Invalid credentials"}, status=400)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials"}, status=400)


class UserLogoutView(APIView):
    def post(self, request):
        response = Response({"detail": "Logout successful"})
        response.delete_cookie('refresh_token')
        return response


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({"detail": "Refresh token not provided"}, status=400)
        
        try:
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)
            return Response({"access": access_token})
        except Exception as e:
            return Response({"detail": "Invalid refresh token"}, status=400)
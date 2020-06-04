import {async, ComponentFixture, TestBed} from '@angular/core/testing';
import {SpinnerModule} from 'src/app/features/spinner/spinner.module';
import {UserTableModule} from 'src/app/features/user-table/user-table.module';
import {InviteUserComponent} from 'src/app/features/invite-user/invite-user.component';
import {UserListComponent} from './user-list.component';
import {UserListFacade} from './user-list-facade';
import {of} from 'rxjs';
import {InviteUserModule} from '../invite-user/invite-user.module';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {FormsModule} from '@angular/forms';
import {UserTablePipeModule} from '../../ui/search-pipe/user-table-filter.module';
import {MatInputModule} from '@angular/material/input';
import {CommonModule} from '@angular/common';
import {SnackBarService} from '../snackbar/snackbar.service';
import {InviteDialogModule} from '../invite-dialog/invite-dialog.module';
import {MatDialogModule} from '@angular/material';


describe('UserListComponent', () => {
  let component: UserListComponent;
  let fixture: ComponentFixture<UserListComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [
        NoopAnimationsModule,
        CommonModule,
        UserTableModule,
        SpinnerModule,
        InviteUserModule,
        FormsModule,
        UserTablePipeModule,
        MatInputModule,
        MatDialogModule,
        InviteDialogModule
      ],
      declarations: [UserListComponent],
      providers: [
        {
          provide: SnackBarService,
          useValue: {}
        }, {
          provide: UserListFacade,
          useValue: {
            initSubscriptions: () => of([{}]),
            users$: of([{
              id: 0,
              name: 'name',
              owner: {
                firstname: 'firstname'
              }
            }]),
            selectedOrganization$: of([{}]),
            isLoading$: of([{}]),
            availableRoles$: of([{}]),
            unsubscribe() { }
          }
        }],
    })
      .overrideComponent(InviteUserComponent, {
        set: {}
      })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UserListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});